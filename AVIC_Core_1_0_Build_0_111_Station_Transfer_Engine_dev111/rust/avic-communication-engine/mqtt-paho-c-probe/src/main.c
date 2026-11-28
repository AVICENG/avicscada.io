#include <MQTTAsync.h>

#include <stdio.h>
#include <string.h>

static int message_arrived(void *context, char *topic_name, int topic_len,
                           MQTTAsync_message *message)
{
    (void)context;
    (void)topic_name;
    (void)topic_len;
    if (message != NULL) {
        MQTTAsync_freeMessage(&message);
    }
    return 1;
}

static void connection_lost(void *context, char *cause)
{
    (void)context;
    (void)cause;
}

static void delivery_complete(void *context, MQTTAsync_token token)
{
    (void)context;
    (void)token;
}

static int self_test(void)
{
    MQTTAsync client = NULL;
    int rc = MQTTAsync_create(&client, "tcp://127.0.0.1:1883",
                              "avic-mqtt-c-probe",
                              MQTTCLIENT_PERSISTENCE_NONE, NULL);
    if (rc != MQTTASYNC_SUCCESS || client == NULL) {
        fprintf(stderr, "MQTTAsync_create failed: %d\\n", rc);
        return 1;
    }

    rc = MQTTAsync_setCallbacks(client, NULL, connection_lost,
                                message_arrived, delivery_complete);
    if (rc != MQTTASYNC_SUCCESS) {
        fprintf(stderr, "MQTTAsync_setCallbacks failed: %d\\n", rc);
        MQTTAsync_destroy(&client);
        return 1;
    }

    MQTTAsync_destroy(&client);
    if (client != NULL) {
        fprintf(stderr, "MQTTAsync_destroy did not clear client handle\\n");
        return 1;
    }

    printf("paho_mqtt_c=%s async_create=ok callbacks=ok destroy=ok mqtt311=%d mqtt5=%d\\n",
           MQTTAsync_getVersionInfo()[0].value,
           MQTTVERSION_3_1_1, MQTTVERSION_5);
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 2 || strcmp(argv[1], "--self-test") != 0) {
        fprintf(stderr, "Usage: %s --self-test\\n", argv[0]);
        return 64;
    }
    return self_test();
}
