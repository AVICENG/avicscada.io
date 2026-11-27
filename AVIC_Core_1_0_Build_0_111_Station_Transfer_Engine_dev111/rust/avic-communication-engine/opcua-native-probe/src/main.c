#include <open62541/client.h>
#include <open62541/client_config_default.h>
#include <open62541/client_highlevel.h>
#include <open62541/types.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_INPUT_FILE (1024u * 1024u)
#define MAX_BROWSE_CHILDREN 500u

static int read_file(const char *path, UA_ByteString *out) {
    FILE *file = fopen(path, "rb");
    if(!file)
        return 0;
    if(fseek(file, 0, SEEK_END) != 0) {
        fclose(file);
        return 0;
    }
    long length = ftell(file);
    if(length <= 0 || (unsigned long)length > MAX_INPUT_FILE ||
       fseek(file, 0, SEEK_SET) != 0) {
        fclose(file);
        return 0;
    }
    UA_StatusCode status = UA_ByteString_allocBuffer(out, (size_t)length);
    if(status != UA_STATUSCODE_GOOD) {
        fclose(file);
        return 0;
    }
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
        if(strcmp(policy, allowed[i]) == 0)
            return 1;
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
    for(size_t i = 0; i < length; ++i) {
        unsigned char ch = (unsigned char)authority[i];
        if(ch <= 0x20 || ch == 0x7f)
            return 0;
    }

    const char *port_text = NULL;
    if(authority[0] == '[') {
        const char *close = (const char *)memchr(authority, ']', length);
        if(!close || close + 1 >= authority + length || close[1] != ':')
            return 0;
        port_text = close + 2;
    } else {
        const char *colon = (const char *)memchr(authority, ':', length);
        if(!colon || memchr(colon + 1, ':',
                            (size_t)((authority + length) - (colon + 1))))
            return 0;
        if(colon == authority)
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
    port_buffer[port_length] = '\0';
    for(size_t i = 0; i < port_length; ++i)
        if(port_buffer[i] < '0' || port_buffer[i] > '9')
            return 0;
    char *parse_end = NULL;
    unsigned long port = strtoul(port_buffer, &parse_end, 10);
    return parse_end != port_buffer && *parse_end == '\0' && port >= 1 && port <= 65535;
}

static int security_self_test(void) {
    static const char *const policies[] = {
        "http://opcfoundation.org/UA/SecurityPolicy#Basic256Sha256",
        "http://opcfoundation.org/UA/SecurityPolicy#Aes128_Sha256_RsaOaep",
        "http://opcfoundation.org/UA/SecurityPolicy#Aes256_Sha256_RsaPss"
    };
    for(size_t i = 0; i < sizeof(policies) / sizeof(policies[0]); ++i)
        if(!policy_allowed(policies[i]))
            return 1;

    if(policy_allowed("http://opcfoundation.org/UA/SecurityPolicy#None") ||
       endpoint_allowed("opc.tcp://host") ||
       endpoint_allowed("opc.tcp://user@host:4840") ||
       endpoint_allowed("opc.tcp://host:0") ||
       endpoint_allowed("opc.tcp://host:70000") ||
       endpoint_allowed("opc.tcp://host:abc") ||
       !endpoint_allowed("opc.tcp://127.0.0.1:4840/UA/Plant") ||
       !endpoint_allowed("opc.tcp://[::1]:4840/UA/Plant")) {
        fprintf(stderr, "security self-test failed\n");
        return 1;
    }
    return 0;
}

static UA_StatusCode validate_numeric_nodeid(const char *identifier) {
    if(strncmp(identifier, "i=", 2) != 0)
        return UA_STATUSCODE_GOOD;

    const char *cursor = identifier + 2;
    if(*cursor < '0' || *cursor > '9')
        return UA_STATUSCODE_BADINVALIDARGUMENT;

    /* UA_NodeId numeric identifiers are UInt32. Check before open62541 parses
       the text: some parser paths can narrow an overflowing decimal value. */
    unsigned long long value = 0;
    while(*cursor >= '0' && *cursor <= '9') {
        unsigned long long digit = (unsigned long long)(*cursor - '0');
        if(value > (4294967295ULL - digit) / 10ULL)
            return UA_STATUSCODE_BADOUTOFRANGE;
        value = value * 10ULL + digit;
        ++cursor;
    }
    if(*cursor != '\0')
        return UA_STATUSCODE_BADINVALIDARGUMENT;
    return UA_STATUSCODE_GOOD;
}

static UA_StatusCode parse_nodeid_checked(UA_NodeId *node, const char *text) {
    if(!text || strncmp(text, "ns=", 3) != 0)
        return UA_STATUSCODE_BADINVALIDARGUMENT;
    const char *cursor = text + 3;
    if(*cursor < '0' || *cursor > '9')
        return UA_STATUSCODE_BADINVALIDARGUMENT;
    unsigned int namespace_index = 0;
    while(*cursor >= '0' && *cursor <= '9') {
        unsigned int digit = (unsigned int)(*cursor - '0');
        if(namespace_index > (65535u - digit) / 10u)
            return UA_STATUSCODE_BADOUTOFRANGE;
        namespace_index = namespace_index * 10u + digit;
        ++cursor;
    }
    if(*cursor != ';')
        return UA_STATUSCODE_BADINVALIDARGUMENT;
    UA_StatusCode numeric_status = validate_numeric_nodeid(cursor + 1);
    if(numeric_status != UA_STATUSCODE_GOOD)
        return numeric_status;
    UA_String input = UA_STRING_ALLOC(text);
    if(!input.data)
        return UA_STATUSCODE_BADOUTOFMEMORY;
    UA_StatusCode status = UA_NodeId_parse(node, input);
    UA_String_clear(&input);
    return status;
}

static int nodeid_self_test(void) {
    if(security_self_test() != 0)
        return 1;

    static const char *const valid[] = {
        "ns=0;i=2258",
        "ns=1;i=4294967295",
        "ns=2;s=AHU.SupplyAirTemp",
        "ns=2;g=00112233-4455-6677-8899-aabbccddeeff",
        "ns=3;b=YWJj"
    };
    for(size_t i = 0; i < sizeof(valid) / sizeof(valid[0]); ++i) {
        UA_NodeId node;
        UA_NodeId_init(&node);
        UA_StatusCode status = parse_nodeid_checked(&node, valid[i]);
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
        "ns=1;i=18446744073709551615", "ns=1;i=1x", "ns=1;i=",
        "ns=1;g=not-a-guid", "ns=1;b=***", "i=123", "ns=1;x=1"
    };
    for(size_t i = 0; i < sizeof(invalid) / sizeof(invalid[0]); ++i) {
        UA_NodeId node;
        UA_NodeId_init(&node);
        UA_StatusCode status = parse_nodeid_checked(&node, invalid[i]);
        if(status == UA_STATUSCODE_GOOD) {
            fprintf(stderr, "Invalid NodeId unexpectedly accepted: %s\n", invalid[i]);
            UA_NodeId_clear(&node);
            return 1;
        }
        UA_NodeId_clear(&node);
    }

    puts("opcua_native_probe=self_test_ok nodeid_forms=4 invalid_rejected=10 secure_policies=3 endpoint_validation=ok security_none=forbidden");
    return 0;
}

static void print_json_string(const UA_String *value) {
    putchar('"');
    for(size_t i = 0; i < value->length; ++i) {
        unsigned char ch = value->data[i];
        if(ch == '"' || ch == '\\') {
            putchar('\\');
            putchar((int)ch);
        } else if(ch < 0x20) {
            printf("\\u%04x", (unsigned int)ch);
        } else {
            putchar((int)ch);
        }
    }
    putchar('"');
}

static void print_browse_reference(const UA_ReferenceDescription *reference) {
    UA_String node_id_text = UA_STRING_NULL;
    UA_StatusCode node_status = UA_NodeId_print(&reference->nodeId.nodeId, &node_id_text);
    printf("{\"node_id\":");
    if(node_status == UA_STATUSCODE_GOOD)
        print_json_string(&node_id_text);
    else
        printf("\"\"");
    printf(",\"display_name\":");
    print_json_string(&reference->displayName.text);
    printf(",\"node_class\":%u", (unsigned int)reference->nodeClass);
    if(reference->nodeId.namespaceUri.length > 0) {
        printf(",\"namespace_uri\":");
        print_json_string(&reference->nodeId.namespaceUri);
    }
    printf(",\"server_index\":%u}", (unsigned int)reference->nodeId.serverIndex);
    UA_String_clear(&node_id_text);
}

static int browse_children(UA_Client *client, const UA_NodeId *parent) {
    UA_BrowseRequest request;
    UA_BrowseRequest_init(&request);
    request.requestedMaxReferencesPerNode = MAX_BROWSE_CHILDREN;
    request.nodesToBrowse = UA_BrowseDescription_new();
    if(!request.nodesToBrowse)
        return 1;
    request.nodesToBrowseSize = 1;
    UA_BrowseDescription *description = &request.nodesToBrowse[0];
    UA_StatusCode status = UA_NodeId_copy(parent, &description->nodeId);
    if(status != UA_STATUSCODE_GOOD) {
        UA_BrowseRequest_clear(&request);
        return 1;
    }
    description->browseDirection = UA_BROWSEDIRECTION_FORWARD;
    description->referenceTypeId = UA_NODEID_NUMERIC(0, UA_NS0ID_HIERARCHICALREFERENCES);
    description->includeSubtypes = true;
    description->resultMask = UA_BROWSERESULTMASK_DISPLAYNAME | UA_BROWSERESULTMASK_NODECLASS;

    UA_BrowseResponse response = UA_Client_Service_browse(client, request);
    UA_BrowseRequest_clear(&request);
    status = response.responseHeader.serviceResult;
    if(status != UA_STATUSCODE_GOOD || response.resultsSize != 1) {
        fprintf(stderr, "OPC UA Browse service failed: %s\n",
                UA_StatusCode_name(status == UA_STATUSCODE_GOOD
                                   ? UA_STATUSCODE_BADUNEXPECTEDERROR : status));
        UA_BrowseResponse_clear(&response);
        return 1;
    }

    UA_BrowseResult *result = &response.results[0];
    if(result->statusCode != UA_STATUSCODE_GOOD) {
        fprintf(stderr, "OPC UA Browse result failed: %s\n",
                UA_StatusCode_name(result->statusCode));
        UA_BrowseResponse_clear(&response);
        return 1;
    }

    size_t count = result->referencesSize;
    if(count > MAX_BROWSE_CHILDREN)
        count = MAX_BROWSE_CHILDREN;
    printf("{\"browse\":[");
    for(size_t i = 0; i < count; ++i) {
        if(i > 0)
            putchar(',');
        print_browse_reference(&result->references[i]);
    }
    UA_Boolean has_more = result->continuationPoint.length > 0 ||
                          result->referencesSize > MAX_BROWSE_CHILDREN;
    if(result->continuationPoint.length > 0) {
        /* Release server-side continuation state without retrieving another page. */
        UA_BrowseNextRequest release_request;
        UA_BrowseNextRequest_init(&release_request);
        release_request.releaseContinuationPoints = true;
        release_request.continuationPointsSize = 1;
        release_request.continuationPoints = &result->continuationPoint;
        UA_BrowseNextResponse release_response =
            UA_Client_Service_browseNext(client, release_request);
        if(release_response.responseHeader.serviceResult != UA_STATUSCODE_GOOD)
            fprintf(stderr, "OPC UA BrowseNext continuation release failed: %s\n",
                    UA_StatusCode_name(release_response.responseHeader.serviceResult));
        UA_BrowseNextResponse_clear(&release_response);
    }
    printf("],\"count\":%zu,\"has_more\":%s}\n",
           count, has_more ? "true" : "false");
    UA_BrowseResponse_clear(&response);
    if(has_more)
        fprintf(stderr, "OPC UA Browse result capped at %u; continuation was released\n",
                (unsigned int)MAX_BROWSE_CHILDREN);
    return 0;
}

static int connect_and_execute(int argc, char **argv, int browse) {
    if(argc != 10) {
        fprintf(stderr, "usage: %s <--read|--browse> <endpoint> <client-cert.der> <client-key.der> "
                "<trusted-server.der> <application-uri> <policy-uri> <Sign|SignAndEncrypt> <NodeId>\n",
                argv[0]);
        return 2;
    }

    const char *endpoint = argv[2];
    const char *cert_path = argv[3];
    const char *key_path = argv[4];
    const char *trust_path = argv[5];
    const char *app_uri = argv[6];
    const char *policy = argv[7];
    const char *mode = argv[8];
    const char *nodeid_text = argv[9];

    if(!endpoint_allowed(endpoint) || !policy_allowed(policy) ||
       (strcmp(mode, "Sign") != 0 && strcmp(mode, "SignAndEncrypt") != 0) ||
       strncmp(app_uri, "urn:", 4) != 0) {
        fprintf(stderr, "configuration rejected; SecurityPolicy None is forbidden\n");
        return 2;
    }

    UA_ByteString cert = UA_BYTESTRING_NULL;
    UA_ByteString key = UA_BYTESTRING_NULL;
    UA_ByteString trust = UA_BYTESTRING_NULL;
    if(!read_file(cert_path, &cert) || !read_file(key_path, &key) ||
       !read_file(trust_path, &trust)) {
        fprintf(stderr, "certificate, private key or trust certificate could not be read\n");
        UA_ByteString_clear(&cert);
        UA_ByteString_clear(&key);
        UA_ByteString_clear(&trust);
        return 2;
    }

    UA_Client *client = UA_Client_new();
    if(!client) {
        UA_ByteString_clear(&cert);
        UA_ByteString_clear(&key);
        UA_ByteString_clear(&trust);
        return 3;
    }

    UA_ClientConfig *config = UA_Client_getConfig(client);
    UA_StatusCode status = UA_ClientConfig_setDefaultEncryption(
        config, cert, key, &trust, 1, NULL, 0);
    UA_ByteString_clear(&cert);
    UA_ByteString_clear(&key);
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
    config->clientDescription.applicationUri = UA_String_fromChars(app_uri);
    config->timeout = 5000;
    config->localConnectionConfig.localMaxMessageSize = 4u * 1024u * 1024u;
    config->localConnectionConfig.localMaxChunkCount = 64u;

    status = UA_Client_connect(client, endpoint);
    if(status != UA_STATUSCODE_GOOD) {
        fprintf(stderr, "secure OPC UA connection failed: %s\n", UA_StatusCode_name(status));
        UA_Client_delete(client);
        return 4;
    }

    UA_NodeId node;
    UA_NodeId_init(&node);
    status = parse_nodeid_checked(&node, nodeid_text);
    if(status != UA_STATUSCODE_GOOD) {
        fprintf(stderr, "NodeId rejected: %s\n", UA_StatusCode_name(status));
        UA_NodeId_clear(&node);
        UA_Client_disconnect(client);
        UA_Client_delete(client);
        return 5;
    }

    if(browse) {
        int browse_status = browse_children(client, &node);
        UA_NodeId_clear(&node);
        UA_Client_disconnect(client);
        UA_Client_delete(client);
        return browse_status == 0 ? 0 : 7;
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
    UA_Variant_clear(&value);
    UA_NodeId_clear(&node);
    UA_Client_disconnect(client);
    UA_Client_delete(client);
    return status == UA_STATUSCODE_GOOD ? 0 : 6;
}

int main(int argc, char **argv) {
    if(argc == 2 && strcmp(argv[1], "--self-test") == 0)
        return nodeid_self_test();
    if(argc > 1 && strcmp(argv[1], "--read") == 0)
        return connect_and_execute(argc, argv, 0);
    if(argc > 1 && strcmp(argv[1], "--browse") == 0)
        return connect_and_execute(argc, argv, 1);
    fprintf(stderr, "AVIC OPC UA native probe (open62541 1.4.21)\n"
            "  --self-test\n"
            "  --read <endpoint> <cert.der> <key.der> <trusted-server.der> "
            "<application-uri> <policy-uri> <Sign|SignAndEncrypt> <NodeId>\n"
            "  --browse <endpoint> <cert.der> <key.der> <trusted-server.der> "
            "<application-uri> <policy-uri> <Sign|SignAndEncrypt> <parent-NodeId>\n");
    return 2;
}
