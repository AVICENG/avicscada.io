#define _POSIX_C_SOURCE 200809L
#include <jansson.h>
#include <modbus.h>
#include <stdint.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#include <rpc.h>
#else
#include <uuid/uuid.h>
#endif

#define MAX_FRAME (1024u * 1024u)

typedef struct {
    char installation_id[129], project_id[129], station_id[129];
    char driver_instance_id[129], worker_id[37];
    uint64_t generation;
    uint64_t outgoing_sequence;
    int initialized, configured, started;
    char protocol[32];
    char host[256];
    int port, unit_id, timeout_ms;
    modbus_t *modbus;
} worker_t;

static int read_exact(FILE *stream, uint8_t *buffer, size_t length) {
    size_t done = 0;
    while (done < length) {
        size_t n = fread(buffer + done, 1, length - done, stream);
        if (n == 0) return 0;
        done += n;
    }
    return 1;
}

static int write_exact(FILE *stream, const uint8_t *buffer, size_t length) {
    size_t done = 0;
    while (done < length) {
        size_t n = fwrite(buffer + done, 1, length - done, stream);
        if (n == 0) return 0;
        done += n;
    }
    return fflush(stream) == 0;
}

static int read_frame(json_t **out) {
    uint8_t header[4];
    int first = fgetc(stdin);
    if (first == EOF) return feof(stdin) ? 0 : -1;
    header[0] = (uint8_t)first;
    if (!read_exact(stdin, header + 1, 3)) return -1;
    uint32_t length = ((uint32_t)header[0] << 24) | ((uint32_t)header[1] << 16)
                    | ((uint32_t)header[2] << 8) | (uint32_t)header[3];
    if (length == 0 || length > MAX_FRAME) return -1;
    char *body = (char *)malloc((size_t)length);
    if (!body) return -1;
    if (!read_exact(stdin, (uint8_t *)body, length)) { free(body); return -1; }
    json_error_t error;
    *out = json_loadb(body, length, JSON_REJECT_DUPLICATES, &error);
    free(body);
    return *out && json_is_object(*out) ? 1 : -1;
}

static int write_frame(json_t *value) {
    char *body = json_dumps(value, JSON_COMPACT | JSON_ENSURE_ASCII);
    if (!body) return 0;
    size_t length = strlen(body);
    if (length == 0 || length > MAX_FRAME) { free(body); return 0; }
    uint8_t header[4] = {
        (uint8_t)(length >> 24), (uint8_t)(length >> 16),
        (uint8_t)(length >> 8), (uint8_t)length
    };
    int ok = write_exact(stdout, header, sizeof(header))
          && write_exact(stdout, (const uint8_t *)body, length);
    free(body);
    return ok;
}

static int make_uuid(char out[37]) {
#ifdef _WIN32
    UUID id;
    RPC_STATUS status = UuidCreate(&id);
    if (status != RPC_S_OK && status != RPC_S_UUID_LOCAL_ONLY) return 0;
    RPC_CSTR text = NULL;
    if (UuidToStringA(&id, &text) != RPC_S_OK || !text) return 0;
    strncpy(out, (const char *)text, 36);
    out[36] = '\0';
    RpcStringFreeA(&text);
#else
    uuid_t id;
    uuid_generate_random(id);
    uuid_unparse_lower(id, out);
#endif
    return 1;
}

static const char *get_string(json_t *object, const char *key) {
    json_t *value = json_object_get(object, key);
    return json_is_string(value) ? json_string_value(value) : NULL;
}
static int get_int(json_t *object, const char *key, json_int_t *out) {
    json_t *value = json_object_get(object, key);
    if (!json_is_integer(value)) return 0;
    *out = json_integer_value(value);
    return 1;
}
static int copy_required(char *dst, size_t cap, json_t *object, const char *key) {
    const char *value = get_string(object, key);
    if (!value || !*value || strlen(value) >= cap) return 0;
    strcpy(dst, value);
    return 1;
}
static int valid_uuid(const char *s) {
    if (!s || strlen(s) != 36) return 0;
    for (int i = 0; i < 36; ++i) {
        if (i == 8 || i == 13 || i == 18 || i == 23) { if (s[i] != '-') return 0; }
        else if (!((s[i] >= '0' && s[i] <= '9') || (s[i] >= 'a' && s[i] <= 'f')
                || (s[i] >= 'A' && s[i] <= 'F'))) return 0;
    }
    return 1;
}

static int contains_secret_key(json_t *value) {
    if (json_is_object(value)) {
        const char *key;
        json_t *child;
        json_object_foreach(value, key, child) {
            char normalized[96];
            size_t n = 0;
            for (const char *p = key; *p && n < sizeof(normalized)-1; ++p)
                if ((*p >= 'A' && *p <= 'Z') || (*p >= 'a' && *p <= 'z'))
                    normalized[n++] = (char)((*p >= 'A' && *p <= 'Z') ? *p + 32 : *p);
            normalized[n] = '\0';
            if (strstr(normalized, "password") || strstr(normalized, "secret")
                || strstr(normalized, "token") || strstr(normalized, "credential")
                || strstr(normalized, "privatekey") || strstr(normalized, "apikey")
                || contains_secret_key(child)) return 1;
        }
    } else if (json_is_array(value)) {
        size_t i; json_t *child;
        json_array_foreach(value, i, child) if (contains_secret_key(child)) return 1;
    }
    return 0;
}

static void close_modbus(worker_t *w) {
    if (w->modbus) { modbus_close(w->modbus); modbus_free(w->modbus); w->modbus = NULL; }
}
static int connect_modbus(worker_t *w) {
    if (w->modbus) return 1;
    w->modbus = modbus_new_tcp(w->host, w->port);
    if (!w->modbus) return 0;
    uint32_t sec = (uint32_t)(w->timeout_ms / 1000);
    uint32_t usec = (uint32_t)(w->timeout_ms % 1000) * 1000u;
    if (modbus_set_slave(w->modbus, w->unit_id) == -1
        || modbus_set_response_timeout(w->modbus, sec, usec) == -1
        || modbus_connect(w->modbus) == -1) {
        close_modbus(w); return 0;
    }
    return 1;
}

static json_t *error_payload(const char *code, const char *message) {
    json_t *p = json_object();
    json_object_set_new(p, "code", json_string(code));
    json_object_set_new(p, "message", json_string(message));
    return p;
}

static json_t *handle_read(worker_t *w, json_t *payload, const char **kind) {
    json_int_t port, unit, timeout, function, address, count;
    const char *protocol = get_string(payload, "protocol");
    const char *host = get_string(payload, "host");
    if (!protocol || strcmp(protocol, "modbus-tcp") != 0 || strcmp(w->protocol, "modbus-tcp") != 0)
        return error_payload("PROTOCOL_SCOPE_MISMATCH", "Only configured modbus-tcp is supported");
    if (!host || strcmp(host, w->host) != 0
        || !get_int(payload, "port", &port) || port != w->port
        || !get_int(payload, "unit_id", &unit) || unit != w->unit_id
        || !get_int(payload, "timeout_ms", &timeout) || timeout != w->timeout_ms
        || !get_int(payload, "function", &function)
        || !get_int(payload, "address", &address)
        || !get_int(payload, "count", &count))
        return error_payload("INVALID_READ", "Invalid or mismatched Modbus read parameters");
    if (address < 0 || address > 65535 || count < 1
        || function < 1 || function > 4
        || (function <= 2 && count > 2000) || (function >= 3 && count > 125)
        || address + count > 65536)
        return error_payload("READ_OUT_OF_RANGE", "Modbus function/address/count out of range");
    if (!connect_modbus(w)) {
        close_modbus(w); *kind = "read_error";
        return error_payload("CONNECTION_FAILED", "libmodbus connection failed");
    }
    json_t *values = json_array();
    int rc = -1;
    if (function == 1 || function == 2) {
        uint8_t *bits = (uint8_t *)calloc((size_t)count, 1);
        if (bits) {
            rc = function == 1 ? modbus_read_bits(w->modbus, (int)address, (int)count, bits)
                               : modbus_read_input_bits(w->modbus, (int)address, (int)count, bits);
            if (rc == count) for (int i = 0; i < rc; ++i)
                json_array_append_new(values, json_boolean(bits[i] != 0));
            free(bits);
        }
    } else {
        uint16_t *regs = (uint16_t *)calloc((size_t)count, sizeof(uint16_t));
        if (regs) {
            rc = function == 3 ? modbus_read_registers(w->modbus, (int)address, (int)count, regs)
                               : modbus_read_input_registers(w->modbus, (int)address, (int)count, regs);
            if (rc == count) for (int i = 0; i < rc; ++i)
                json_array_append_new(values, json_integer(regs[i]));
            free(regs);
        }
    }
    if (rc != count) {
        int err = errno;
        close_modbus(w);
        json_decref(values);
        char message[256];
        snprintf(message, sizeof(message), "libmodbus read failed (errno=%d)", err);
        *kind = "read_error";
        return error_payload("MODBUS_READ_FAILED", message);
    }
    json_t *result = json_object();
    json_object_set_new(result, "function", json_integer(function));
    json_object_set_new(result, "values", values);
    json_t *response = json_object();
    json_object_set_new(response, "transport_ok", json_true());
    json_object_set_new(response, "result", result);
    *kind = "read_result";
    return response;
}

static json_t *make_response(worker_t *w, json_t *request, const char *kind, json_t *payload) {
    json_t *response = json_deep_copy(request);
    if (!response) return NULL;
    char id[37];
    if (!make_uuid(id)) { json_decref(response); return NULL; }
    json_object_set_new(response, "message_id", json_string(id));
    json_object_set_new(response, "kind", json_string(kind));
    json_object_set_new(response, "sequence", json_integer((json_int_t)++w->outgoing_sequence));
    json_object_set_new(response, "correlation_id", json_deep_copy(json_object_get(request, "message_id")));
    json_object_set_new(response, "payload", payload);
    return response;
}

static int same_scope(worker_t *w, json_t *request) {
    json_int_t generation;
    return copy_required(w->installation_id, sizeof(w->installation_id), request, "installation_id")
        && copy_required(w->project_id, sizeof(w->project_id), request, "project_id")
        && copy_required(w->station_id, sizeof(w->station_id), request, "station_id")
        && copy_required(w->driver_instance_id, sizeof(w->driver_instance_id), request, "driver_instance_id")
        && copy_required(w->worker_id, sizeof(w->worker_id), request, "worker_id")
        && valid_uuid(w->worker_id) && get_int(request, "generation", &generation)
        && generation > 0 && (w->generation = (uint64_t)generation) > 0;
}
static int check_scope(worker_t *w, json_t *request) {
    json_int_t generation;
    return get_int(request, "generation", &generation) && generation > 0
        && (uint64_t)generation == w->generation
        && get_string(request, "installation_id") && strcmp(get_string(request, "installation_id"), w->installation_id) == 0
        && get_string(request, "project_id") && strcmp(get_string(request, "project_id"), w->project_id) == 0
        && get_string(request, "station_id") && strcmp(get_string(request, "station_id"), w->station_id) == 0
        && get_string(request, "driver_instance_id") && strcmp(get_string(request, "driver_instance_id"), w->driver_instance_id) == 0
        && get_string(request, "worker_id") && strcmp(get_string(request, "worker_id"), w->worker_id) == 0;
}

static int process(worker_t *w, json_t *request, int *exit_after) {
    const char *kind = get_string(request, "kind");
    const char *contract = get_string(request, "contract");
    json_int_t version, sequence;
    json_t *payload = json_object_get(request, "payload");
    if (!kind || !contract || strcmp(contract, "avic.driver.ipc") != 0
        || !get_int(request, "version", &version) || version != 1
        || !get_int(request, "sequence", &sequence) || sequence < 0
        || !json_is_object(payload) || !valid_uuid(get_string(request, "message_id"))) return 0;
    if (!w->initialized) {
        if (strcmp(kind, "initialize") != 0 || !same_scope(w, request)) return 0;
        w->initialized = 1;
    } else if (!check_scope(w, request)) return 0;

    const char *response_kind = "error";
    json_t *response_payload = NULL;
    if (strcmp(kind, "initialize") == 0) {
        response_kind = "initialized";
        response_payload = json_pack("{s:s,s:i,s:s}", "protocol", "avic.driver.ipc",
                                     "version", 1, "worker_version", "0.1.0");
    } else if (strcmp(kind, "configure") == 0) {
        if (w->started || contains_secret_key(payload)) {
            response_payload = error_payload("INVALID_CONFIGURATION", "Worker running or secret field present");
        } else {
            const char *protocol = get_string(payload, "protocol");
            if (protocol && strcmp(protocol, "modbus-tcp") == 0
                && copy_required(w->host, sizeof(w->host), payload, "host")
                && get_int(payload, "port", &version) && version > 0 && version <= 65535
                && get_int(payload, "unit_id", &sequence) && sequence >= 0 && sequence <= 247) {
                w->port = (int)version; w->unit_id = (int)sequence;
                w->timeout_ms = 2000;
                if (get_int(payload, "timeout_ms", &version) && version >= 100 && version <= 10000)
                    w->timeout_ms = (int)version;
                strcpy(w->protocol, protocol); w->configured = 1;
                response_kind = "configured";
                response_payload = json_pack("{s:b,s:s}", "configured", 1, "protocol", protocol);
            } else response_payload = error_payload("INVALID_CONFIGURATION", "Invalid Modbus TCP configuration");
        }
    } else if (strcmp(kind, "start") == 0) {
        if (!w->configured) response_payload = error_payload("CONFIGURE_REQUIRED", "Configure worker first");
        else { w->started = 1; response_kind = "status";
               response_payload = json_pack("{s:s,s:b}", "state", "RUNNING", "write_supported", 0); }
    } else if (strcmp(kind, "read") == 0) {
        if (!w->started) response_payload = error_payload("DRIVER_NOT_RUNNING", "Worker is not running");
        else if (contains_secret_key(payload)) response_payload = error_payload("SECRET_IN_REQUEST", "Secret field rejected");
        else response_payload = handle_read(w, payload, &response_kind);
    } else if (strcmp(kind, "stop") == 0) {
        w->started = 0; close_modbus(w); response_kind = "status";
        response_payload = json_pack("{s:s,s:b}", "state", "STOPPED", "write_supported", 0);
    } else if (strcmp(kind, "get_status") == 0) {
        response_kind = "status";
        response_payload = json_pack("{s:s,s:b,s:b}", "state", w->started ? "RUNNING" : "STOPPED",
                                     "configured", w->configured, "write_supported", 0);
    } else if (strcmp(kind, "shutdown") == 0) {
        w->started = 0; close_modbus(w); response_kind = "status"; *exit_after = 1;
        response_payload = json_pack("{s:s,s:b}", "state", "STOPPED", "shutdown", 1);
    } else if (strcmp(kind, "write") == 0 || strcmp(kind, "write_point") == 0) {
        response_payload = error_payload("WRITE_DISABLED", "Field writes are disabled in Worker v1");
    } else {
        response_payload = error_payload("UNKNOWN_COMMAND", "Unsupported IPC command");
    }
    if (!response_payload) return 0;
    json_t *response = make_response(w, request, response_kind, response_payload);
    if (!response) return 0;
    int ok = write_frame(response);
    json_decref(response);
    return ok;
}

int main(void) {
    worker_t worker;
    memset(&worker, 0, sizeof(worker));
    for (;;) {
        json_t *request = NULL;
        int status = read_frame(&request);
        if (status == 0) break;
        if (status < 0) { close_modbus(&worker); return 2; }
        int should_exit = 0;
        int ok = process(&worker, request, &should_exit);
        json_decref(request);
        if (!ok) { close_modbus(&worker); return 3; }
        if (should_exit) break;
    }
    close_modbus(&worker);
    return 0;
}
