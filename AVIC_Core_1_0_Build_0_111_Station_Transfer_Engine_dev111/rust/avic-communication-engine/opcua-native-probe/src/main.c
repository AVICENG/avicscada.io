#include <open62541/client.h>
#include <open62541/client_config_default.h>
#include <open62541/client_highlevel.h>
#include <open62541/types.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_INPUT_FILE (1024u * 1024u)

static int read_file(const char *path, UA_ByteString *out) {
    FILE *file = fopen(path, "rb");
    if(!file) return 0;
    if(fseek(file, 0, SEEK_END) != 0) { fclose(file); return 0; }
    long length = ftell(file);
    if(length <= 0 || (unsigned long)length > MAX_INPUT_FILE ||
       fseek(file, 0, SEEK_SET) != 0) { fclose(file); return 0; }
    UA_StatusCode status = UA_ByteString_allocBuffer(out, (size_t)length);
    if(status != UA_STATUSCODE_GOOD) { fclose(file); return 0; }
    size_t count = fread(out->data, 1, (size_t)length, file);
    int close_status = fclose(file);
    if(count != (size_t)length || close_status != 0) {
        UA_ByteString_clear(out);
        return 0;
    }
    return 1;
}

static int policy_allowed(const char *policy) {
    static const char *const allowed[] = {
        "http://opcfoundation.org/UA/SecurityPolicy#Basic256Sha256",
        "http://opcfoundation.org/UA/SecurityPolicy#Aes128_Sha256_RsaOaep",
        "http://opcfoundation.org/UA/SecurityPolicy#Aes256_Sha256_RsaPss"
    };
    for(size_t i = 0; i < sizeof(allowed) / sizeof(allowed[0]); ++i)
        if(strcmp(policy, allowed[i]) == 0) return 1;
    return 0;
}

static int endpoint_allowed(const char *endpoint) {
    if(strncmp(endpoint, "opc.tcp://", 10) != 0 ||
       strchr(endpoint, '?') != NULL || strchr(endpoint, '#') != NULL)
        return 0;
    const char *authority = endpoint + 10;
    const char *end = strpbrk(authority, "/?#");
    size_t length = end ? (size_t)(end - authority) : strlen(authority);
    if(length == 0 || length > 255 || memchr(authority, '@', length) != NULL)
        return 0;
    for(size_t i = 0; i < length; ++i)
        if((unsigned char)authority[i] <= 0x20 || authority[i] == 0x7f)
            return 0;

    const char *port_text = NULL;
    if(authority[0] == '[') {
        const char *close = memchr(authority, ']', length);
        if(!close || close + 1 >= authority + length || close[1] != ':')
            return 0;
        port_text = close + 2;
    } else {
        const char *colon = memchr(authority, ':', length);
        if(!colon || memchr(colon + 1, ':', (size_t)((authority + length) - (colon + 1))))
            return 0;
        port_text = colon + 1;
    }
    if(!port_text || port_text >= authority + length)
        return 0;
    char port_buffer[8];
    size_t port_length = (size_t)((authority + length) - port_text);
    if(port_length == 0 || port_length >= sizeof(port_buffer))
        return 0;
    memcpy(port_buffer, port_text, port_length);
    port_buffer[port_length] = '\\0';
    char *parse_end = NULL;
    unsigned long port = strtoul(port_buffer, &parse_end, 10);
    return parse_end != port_buffer && *parse_end == '\\0' && port >= 1 && port <= 65535;
}

static int security_self_test(void) {
    static const char *const policies[] = {
        "http://opcfoundation.org/UA/SecurityPolicy#Basic256Sha256",
        "http://opcfoundation.org/UA/SecurityPolicy#Aes128_Sha256_RsaOaep",
        "http://opcfoundation.org/UA/SecurityPolicy#Aes256_Sha256_RsaPss"
    };
    for(size_t i = 0; i < sizeof(policies) / sizeof(policies[0]); ++i)
        if(!policy_allowed(policies[i])) return 1;
    if(policy_allowed("http://opcfoundation.org/UA/SecurityPolicy#None") ||
       endpoint_allowed("opc.tcp://host") ||
       endpoint_allowed("opc.tcp://user@host:4840") ||
       endpoint_allowed("opc.tcp://host:0") ||
       endpoint_allowed("opc.tcp://host:70000") ||
       !endpoint_allowed("opc.tcp://127.0.0.1:4840/UA/Plant") ||
       !endpoint_allowed("opc.tcp://[::1]:4840/UA/Plant")) {
        fprintf(stderr, "security self-test failed\\n");
        return 1;
    }
    return 0;
}

static int nodeid_self_test(void) {
    if(security_self_test() != 0)
        return 1;
    static const char *const valid[] = {
        "ns=0;i=2258", "ns=2;s=AHU.SupplyAirTemp",
        "ns=2;g=00112233-4455-6677-8899-aabbccddeeff", "ns=3;b=YWJj"
    };
    for(size_t i = 0; i < sizeof(valid) / sizeof(valid[0]); ++i) {
        UA_NodeId node;
        UA_NodeId_init(&node);
        UA_StatusCode status = UA_NodeId_parse(&node, UA_STRING((char *)valid[i]));
        if(status != UA_STATUSCODE_GOOD) {
            fprintf(stderr, "NodeId self-test failed: %s (%s)\n",
                    valid[i], UA_StatusCode_name(status));
            UA_NodeId_clear(&node);
            return 1;
        }
        UA_NodeId_clear(&node);
    }
    static const char *const invalid[] = {
        "ns=65536;i=1", "ns=1;i=-1", "ns=1;i=4294967296",
        "ns=1;g=not-a-guid", "ns=1;b=***", "i=123", "ns=1;x=1"
    };
    for(size_t i = 0; i < sizeof(invalid) / sizeof(invalid[0]); ++i) {
        UA_NodeId node;
        UA_NodeId_init(&node);
        UA_StatusCode status = UA_NodeId_parse(&node, UA_STRING((char *)invalid[i]));
        if(status == UA_STATUSCODE_GOOD) {
            fprintf(stderr, "Invalid NodeId unexpectedly accepted: %s\n", invalid[i]);
            UA_NodeId_clear(&node);
            return 1;
        }
        UA_NodeId_clear(&node);
    }
    puts("opcua_native_probe=self_test_ok nodeid_forms=4 invalid_rejected=7 secure_policies=3 endpoint_validation=ok security_none=forbidden");
    return 0;
}

static int connect_and_read(int argc, char **argv) {
    if(argc != 10) {
        fprintf(stderr, "usage: %s --connect <endpoint> <client-cert.der> <client-key.der> "
                "<trusted-server.der> <application-uri> <policy-uri> <Sign|SignAndEncrypt> <NodeId>\n",
                argv[0]);
        return 2;
    }
    const char *endpoint = argv[2], *cert_path = argv[3], *key_path = argv[4];
    const char *trust_path = argv[5], *app_uri = argv[6], *policy = argv[7];
    const char *mode = argv[8], *nodeid_text = argv[9];
    if(!endpoint_allowed(endpoint) || !policy_allowed(policy) ||
       (strcmp(mode, "Sign") != 0 && strcmp(mode, "SignAndEncrypt") != 0) ||
       strncmp(app_uri, "urn:", 4) != 0) {
        fprintf(stderr, "configuration rejected; SecurityPolicy None is forbidden\n");
        return 2;
    }

    UA_ByteString cert = UA_BYTESTRING_NULL, key = UA_BYTESTRING_NULL;
    UA_ByteString trust = UA_BYTESTRING_NULL;
    if(!read_file(cert_path, &cert) || !read_file(key_path, &key) ||
       !read_file(trust_path, &trust)) {
        fprintf(stderr, "certificate, private key or trust certificate could not be read\n");
        UA_ByteString_clear(&cert); UA_ByteString_clear(&key);
        UA_ByteString_clear(&trust);
        return 2;
    }

    UA_Client *client = UA_Client_new();
    if(!client) {
        UA_ByteString_clear(&cert); UA_ByteString_clear(&key);
        UA_ByteString_clear(&trust);
        return 3;
    }
    UA_ClientConfig *config = UA_Client_getConfig(client);
    UA_StatusCode status = UA_ClientConfig_setDefaultEncryption(
        config, cert, key, &trust, 1, NULL, 0);
    UA_ByteString_clear(&cert); UA_ByteString_clear(&key);
    UA_ByteString_clear(&trust);
    if(status != UA_STATUSCODE_GOOD) {
        fprintf(stderr, "secure client configuration failed: %s\n", UA_StatusCode_name(status));
        UA_Client_delete(client);
        return 3;
    }

    config->securityMode = strcmp(mode, "Sign") == 0
        ? UA_MESSAGESECURITYMODE_SIGN : UA_MESSAGESECURITYMODE_SIGNANDENCRYPT;
    UA_String_clear(&config->securityPolicyUri);
    config->securityPolicyUri = UA_String_fromChars(policy);
    UA_String_clear(&config->clientDescription.applicationUri);
    config->applicationDescription.applicationUri = UA_String_fromChars(app_uri);
    config->timeout = 5000;

    status = UA_Client_connect(client, endpoint);
    if(status != UA_STATUSCODE_GOOD) {
        fprintf(stderr, "secure OPC UA connection failed: %s\n", UA_StatusCode_name(status));
        UA_Client_delete(client);
        return 4;
    }
    UA_NodeId node;
    UA_NodeId_init(&node);
    status = UA_NodeId_parse(&node, UA_STRING((char *)nodeid_text));
    if(status != UA_STATUSCODE_GOOD) {
        fprintf(stderr, "NodeId rejected: %s\n", UA_StatusCode_name(status));
        UA_NodeId_clear(&node);
        UA_Client_disconnect(client); UA_Client_delete(client);
        return 5;
    }
    UA_Variant value;
    UA_Variant_init(&value);
    status = UA_Client_readValueAttribute(client, node, &value);
    if(status == UA_STATUSCODE_GOOD && value.type != NULL) {
        printf("opcua_native_probe=read_ok node=%s scalar=%s datatype=%s\n",
               nodeid_text, UA_Variant_isScalar(&value) ? "true" : "false",
               value.type->typeName);
    } else {
        fprintf(stderr, "OPC UA Read failed: %s\n", UA_StatusCode_name(status));
    }
    UA_Variant_clear(&value); UA_NodeId_clear(&node);
    UA_Client_disconnect(client); UA_Client_delete(client);
    return status == UA_STATUSCODE_GOOD ? 0 : 6;
}

int main(int argc, char **argv) {
    if(argc == 2 && strcmp(argv[1], "--self-test") == 0)
        return nodeid_self_test();
    if(argc > 1 && strcmp(argv[1], "--connect") == 0)
        return connect_and_read(argc, argv);
    fprintf(stderr, "AVIC OPC UA native probe (open62541 1.4.21)\n"
            "  --self-test\n"
            "  --connect <endpoint> <cert.der> <key.der> <trusted-server.der> "
            "<application-uri> <policy-uri> <Sign|SignAndEncrypt> <NodeId>\n");
    return 2;
}
