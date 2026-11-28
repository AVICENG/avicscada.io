#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include <stdlib.h>
#include <time.h>

#include "bacnet/bacdef.h"
#include "bacnet/bacdcode.h"
#include "bacnet/bactext.h"
#include "bacnet/iam.h"
#include "bacnet/rp.h"
#include "bacnet/version.h"
#include "bacnet/apdu.h"
#include "bacnet/basic/binding/address.h"
#include "bacnet/basic/object/device.h"
#include "bacnet/basic/service/h_iam.h"
#include "bacnet/basic/service/h_apdu.h"
#include "bacnet/basic/service/s_whois.h"
#include "bacnet/basic/service/s_rp.h"
#include "bacnet/basic/tsm/tsm.h"
#include "bacnet/basic/sys/mstimer.h"
#include "bacnet/basic/npdu/h_npdu.h"
#include "bacnet/datalink/datalink.h"
#include "bacnet/datalink/dlenv.h"

#define BACNET_TEST_BUFFER 64u

static int iam_codec_self_test(void)
{
    uint8_t encoded[BACNET_TEST_BUFFER] = { 0 };
    const uint32_t expected_device = 123456u;
    const unsigned expected_max_apdu = 1476u;
    const int expected_segmentation = SEGMENTATION_BOTH;
    const uint16_t expected_vendor = 999u;

    int length = bacnet_iam_request_encode(
        encoded, expected_device, expected_max_apdu,
        expected_segmentation, expected_vendor);
    if (length <= 0 || (size_t)length > sizeof(encoded)) {
        fprintf(stderr, "BACnet I-Am encoder returned invalid length: %d\n", length);
        return 1;
    }

    uint32_t device = 0;
    unsigned max_apdu = 0;
    int segmentation = -1;
    uint16_t vendor = 0;
    int decoded = bacnet_iam_request_decode(
        encoded, (unsigned)length, &device, &max_apdu, &segmentation, &vendor);
    if (decoded != length || device != expected_device ||
        max_apdu != expected_max_apdu ||
        segmentation != expected_segmentation || vendor != expected_vendor) {
        fprintf(stderr,
            "BACnet I-Am round-trip mismatch: decoded=%d device=%u max_apdu=%u segmentation=%d vendor=%u\n",
            decoded, (unsigned)device, max_apdu, segmentation, (unsigned)vendor);
        return 1;
    }

    for (int truncated = 0; truncated < length; ++truncated) {
        if (bacnet_iam_request_decode(
                encoded, (unsigned)truncated, NULL, NULL, NULL, NULL) >= 0) {
            fprintf(stderr, "BACnet I-Am decoder accepted truncated payload: %d/%d\n",
                    truncated, length);
            return 1;
        }
    }

    /* A non-Device object identifier is not a valid I-Am payload. */
    uint8_t invalid_object[BACNET_TEST_BUFFER] = { 0 };
    int object_length = encode_application_object_id(
        invalid_object, OBJECT_ANALOG_INPUT, 1u);
    int offset = object_length;
    offset += encode_application_unsigned(invalid_object + offset, expected_max_apdu);
    offset += encode_application_enumerated(invalid_object + offset,
                                              (uint32_t)expected_segmentation);
    offset += encode_application_unsigned(invalid_object + offset, expected_vendor);
    if (bacnet_iam_request_decode(
            invalid_object, (unsigned)offset, NULL, NULL, NULL, NULL) >= 0) {
        fprintf(stderr, "BACnet I-Am decoder accepted non-Device object identifier\n");
        return 1;
    }

    /* Segmentation enum values outside the BACnet range must be rejected. */
    uint8_t invalid_segmentation[BACNET_TEST_BUFFER] = { 0 };
    offset = encode_application_object_id(
        invalid_segmentation, OBJECT_DEVICE, expected_device);
    offset += encode_application_unsigned(invalid_segmentation + offset, expected_max_apdu);
    offset += encode_application_enumerated(
        invalid_segmentation + offset, MAX_BACNET_SEGMENTATION);
    offset += encode_application_unsigned(invalid_segmentation + offset, expected_vendor);
    if (bacnet_iam_request_decode(
            invalid_segmentation, (unsigned)offset, NULL, NULL, NULL, NULL) >= 0) {
        fprintf(stderr, "BACnet I-Am decoder accepted out-of-range segmentation\\n");
        return 1;
    }

    /* Vendor ID is a 16-bit field; oversized values must be rejected. */
    uint8_t invalid_vendor[BACNET_TEST_BUFFER] = { 0 };
    offset = encode_application_object_id(
        invalid_vendor, OBJECT_DEVICE, expected_device);
    offset += encode_application_unsigned(invalid_vendor + offset, expected_max_apdu);
    offset += encode_application_enumerated(
        invalid_vendor + offset, (uint32_t)expected_segmentation);
    offset += encode_application_unsigned(invalid_vendor + offset, 65536u);
    if (bacnet_iam_request_decode(
            invalid_vendor, (unsigned)offset, NULL, NULL, NULL, NULL) >= 0) {
        fprintf(stderr, "BACnet I-Am decoder accepted vendor ID > 65535\\n");
        return 1;
    }

    printf("bacnet_iam_codec=ok device=%u max_apdu=%u segmentation=%d vendor=%u truncated_payloads_rejected=%d wrong_object_rejected=1 invalid_segmentation_rejected=1 invalid_vendor_rejected=1\\n",
           (unsigned)device, max_apdu, segmentation, (unsigned)vendor, length);
    return 0;
}

static int read_property_codec_self_test(void)
{
    uint8_t encoded[BACNET_TEST_BUFFER] = { 0 };
    BACNET_READ_PROPERTY_DATA request = { 0 };
    request.object_type = OBJECT_ANALOG_INPUT;
    request.object_instance = 42u;
    request.object_property = PROP_PRESENT_VALUE;
    request.array_index = BACNET_ARRAY_ALL;

    int length = read_property_request_encode(encoded, &request);
    if (length <= 0 || (size_t)length > sizeof(encoded)) {
        fprintf(stderr, "BACnet ReadProperty request encoder returned invalid length: %d\\n",
                length);
        return 1;
    }

    BACNET_READ_PROPERTY_DATA decoded = { 0 };
    int decoded_length = rp_decode_service_request(
        encoded, (unsigned)length, &decoded);
    if (decoded_length != length ||
        decoded.object_type != request.object_type ||
        decoded.object_instance != request.object_instance ||
        decoded.object_property != request.object_property ||
        decoded.array_index != request.array_index) {
        fprintf(stderr, "BACnet ReadProperty request round-trip mismatch\\n");
        return 1;
    }

    for (int truncated = 0; truncated < length; ++truncated) {
        BACNET_READ_PROPERTY_DATA partial = { 0 };
        if (rp_decode_service_request(
                encoded, (unsigned)truncated, &partial) >= 0) {
            fprintf(stderr, "BACnet ReadProperty decoder accepted truncated payload: %d/%d\\n",
                    truncated, length);
            return 1;
        }
    }

    printf("bacnet_read_property_codec=ok object_type=%u instance=%u property=%u truncated_payloads_rejected=%d\\n",
           (unsigned)decoded.object_type, (unsigned)decoded.object_instance,
           (unsigned)decoded.object_property, length);
    return 0;
}

static BACNET_ADDRESS Read_Target_Address;
static uint8_t Read_Invoke_ID;
static int Read_Result_State;
static uint8_t Read_Application_Data[1024];
static unsigned Read_Application_Data_Length;

static void read_property_ack_handler(
    uint8_t *service_request,
    uint16_t service_len,
    BACNET_ADDRESS *src,
    BACNET_CONFIRMED_SERVICE_ACK_DATA *service_data)
{
    BACNET_READ_PROPERTY_DATA data = { 0 };
    if (!address_match(&Read_Target_Address, src) ||
        service_data->invoke_id != Read_Invoke_ID) {
        return;
    }
    int decoded = rp_ack_decode_service_request(service_request, service_len, &data);
    if (decoded < 0 || data.application_data_len < 0 ||
        (unsigned)data.application_data_len > sizeof(Read_Application_Data)) {
        Read_Result_State = -1;
        return;
    }
    if (data.application_data_len > 0) {
        memcpy(Read_Application_Data, data.application_data,
               (size_t)data.application_data_len);
    }
    Read_Application_Data_Length = (unsigned)data.application_data_len;
    Read_Result_State = 1;
}

static void read_property_error_handler(
    BACNET_ADDRESS *src,
    uint8_t invoke_id,
    BACNET_ERROR_CLASS error_class,
    BACNET_ERROR_CODE error_code)
{
    if (address_match(&Read_Target_Address, src) && invoke_id == Read_Invoke_ID) {
        fprintf(stderr, "bacnet_read_property_error class=%u code=%u\n",
                (unsigned)error_class, (unsigned)error_code);
        Read_Result_State = -1;
    }
}

static void read_property_abort_handler(
    BACNET_ADDRESS *src, uint8_t invoke_id, uint8_t abort_reason, bool server)
{
    (void)server;
    if (address_match(&Read_Target_Address, src) && invoke_id == Read_Invoke_ID) {
        fprintf(stderr, "bacnet_read_property_abort reason=%u\n",
                (unsigned)abort_reason);
        Read_Result_State = -1;
    }
}

static void read_property_reject_handler(
    BACNET_ADDRESS *src, uint8_t invoke_id, uint8_t reject_reason)
{
    if (address_match(&Read_Target_Address, src) && invoke_id == Read_Invoke_ID) {
        fprintf(stderr, "bacnet_read_property_reject reason=%u\n",
                (unsigned)reject_reason);
        Read_Result_State = -1;
    }
}

static int read_property_transaction(
    uint32_t device_id,
    BACNET_OBJECT_TYPE object_type,
    uint32_t object_instance,
    BACNET_PROPERTY_ID property,
    unsigned timeout_ms)
{
    uint8_t rx_buffer[MAX_MPDU] = { 0 };
    BACNET_ADDRESS source = { 0 };
    struct mstimer deadline = { 0 };
    unsigned max_apdu = 0;
    bool bound = false;
    time_t last_seconds = time(NULL);

    Read_Invoke_ID = 0;
    Read_Result_State = 0;
    Read_Application_Data_Length = 0;
    memset(&Read_Target_Address, 0, sizeof(Read_Target_Address));

    Device_Set_Object_Instance_Number(BACNET_MAX_INSTANCE);
    Device_Init(NULL);
    address_init();
    apdu_set_unconfirmed_handler(SERVICE_UNCONFIRMED_I_AM, handler_i_am_bind);
    apdu_set_confirmed_ack_handler(
        SERVICE_CONFIRMED_READ_PROPERTY, read_property_ack_handler);
    apdu_set_error_handler(
        SERVICE_CONFIRMED_READ_PROPERTY, read_property_error_handler);
    apdu_set_abort_handler(read_property_abort_handler);
    apdu_set_reject_handler(read_property_reject_handler);
    dlenv_init();

    mstimer_set(&deadline, timeout_ms);
    Send_WhoIs(device_id, device_id);

    while (!mstimer_expired(&deadline) && Read_Result_State == 0) {
        uint16_t received = datalink_receive(
            &source, rx_buffer, MAX_MPDU, 100u);
        if (received > 0) {
            npdu_handler(&source, rx_buffer, received);
        }

        time_t now = time(NULL);
        if (now > last_seconds) {
            unsigned long elapsed = (unsigned long)(now - last_seconds);
            uint32_t elapsed_ms = (uint32_t)(elapsed * 1000u);
            while (elapsed_ms > 0u) {
                uint16_t step = elapsed_ms > 60000u ? 60000u : (uint16_t)elapsed_ms;
                tsm_timer_milliseconds(step);
                elapsed_ms -= step;
            }
            while (elapsed > 0u) {
                uint16_t maintenance_step = elapsed > 65535u
                    ? UINT16_MAX : (uint16_t)elapsed;
                datalink_maintenance_timer(maintenance_step);
                elapsed -= maintenance_step;
            }
            last_seconds = now;
        }

        if (!bound) {
            bound = address_bind_request(device_id, &max_apdu, &Read_Target_Address);
        }
        if (bound && Read_Invoke_ID == 0) {
            Read_Invoke_ID = Send_Read_Property_Request(
                device_id, object_type, object_instance, property, BACNET_ARRAY_ALL);
            if (Read_Invoke_ID == 0) {
                fprintf(stderr, "BACnet ReadProperty could not allocate/send transaction\n");
            }
        } else if (Read_Invoke_ID != 0 && tsm_invoke_id_failed(Read_Invoke_ID)) {
            fprintf(stderr, "BACnet ReadProperty TSM timeout invoke_id=%u\n",
                    (unsigned)Read_Invoke_ID);
            tsm_free_invoke_id(Read_Invoke_ID);
            Read_Result_State = -1;
        }
    }

    if (Read_Result_State == 1) {
        printf("bacnet_read_property=ack device_id=%u object_type=%u object_instance=%u property=%u application_data_len=%u value_hex=",
               (unsigned)device_id, (unsigned)object_type,
               (unsigned)object_instance, (unsigned)property,
               Read_Application_Data_Length);
        for (unsigned i = 0; i < Read_Application_Data_Length; ++i) {
            printf("%02x", (unsigned)Read_Application_Data[i]);
        }
        printf("\n");
    } else if (Read_Result_State == 0) {
        fprintf(stderr, "BACnet ReadProperty overall timeout device_id=%u\n",
                (unsigned)device_id);
        if (Read_Invoke_ID != 0 && !tsm_invoke_id_free(Read_Invoke_ID)) {
            tsm_free_invoke_id(Read_Invoke_ID);
        }
    }

    datalink_cleanup();
    return Read_Result_State == 1 ? 0 : 1;
}

static int parse_unsigned(const char *text, unsigned long minimum,
                          unsigned long maximum, unsigned long *value)
{
    char *end = NULL;
    if (!text || !*text) return 0;
    unsigned long parsed = strtoul(text, &end, 10);
    if (!end || *end != '\0' || parsed < minimum || parsed > maximum) return 0;
    *value = parsed;
    return 1;
}

int main(int argc, char **argv)
{
    const char *device_object = bactext_object_type_name(OBJECT_DEVICE);
    if (device_object == NULL) return 2;
    if (iam_codec_self_test() != 0) return 3;
    if (read_property_codec_self_test() != 0) return 4;
    printf("AVIC BACnet Stack C probe: %s; object=%s; codec=self-test-passed\n",
           BACNET_VERSION_TEXT, device_object);

    if (argc == 1) return 0;
    if (argc == 3 && strcmp(argv[1], "--discover-ms") == 0) {
        unsigned long timeout_ms = 0;
        if (!parse_unsigned(argv[2], 100, 30000, &timeout_ms)) {
            fprintf(stderr, "Discovery timeout must be 100..30000 ms\n");
            return 64;
        }
        uint8_t rx_buffer[MAX_MPDU] = { 0 };
        BACNET_ADDRESS source = { 0 };
        BACNET_ADDRESS destination = { 0 };
        struct mstimer deadline = { 0 };
        struct mstimer maintenance = { 0 };
        Device_Set_Object_Instance_Number(BACNET_MAX_INSTANCE);
        Device_Init(NULL);
        address_init();
        apdu_set_unconfirmed_handler(SERVICE_UNCONFIRMED_I_AM, handler_i_am_add);
        dlenv_init();
        mstimer_set(&deadline, (uint32_t)timeout_ms);
        mstimer_set(&maintenance, 1000);
        Send_WhoIs_To_Network(&destination, -1, -1);
        while (!mstimer_expired(&deadline)) {
            uint16_t received = datalink_receive(&source, rx_buffer, MAX_MPDU, 100u);
            if (received > 0) npdu_handler(&source, rx_buffer, received);
            if (mstimer_expired(&maintenance)) {
                datalink_maintenance_timer(1u);
                mstimer_reset(&maintenance);
            }
        }
        unsigned count = address_count();
        printf("bacnet_discovery=complete timeout_ms=%lu devices=%u\n",
               timeout_ms, count);
        for (unsigned index = 0; index < count; ++index) {
            uint32_t device_id = 0;
            unsigned max_apdu = 0;
            BACNET_ADDRESS address = { 0 };
            if (address_get_by_index(index, &device_id, &max_apdu, &address)) {
                printf("device_id=%u max_apdu=%u mac_len=%u network=%u\n",
                       (unsigned)device_id, max_apdu,
                       (unsigned)address.mac_len, (unsigned)address.net);
            }
        }
        datalink_cleanup();
        return 0;
    }
    if (argc == 7 && strcmp(argv[1], "--read-property") == 0) {
        unsigned long device_id = 0, object_type = 0, object_instance = 0;
        unsigned long property = 0, timeout_ms = 0;
        if (!parse_unsigned(argv[2], 0, BACNET_MAX_INSTANCE, &device_id) ||
            !parse_unsigned(argv[3], 0, MAX_BACNET_OBJECT_TYPE - 1, &object_type) ||
            !parse_unsigned(argv[4], 0, BACNET_MAX_INSTANCE, &object_instance) ||
            !parse_unsigned(argv[5], 0, MAX_BACNET_PROPERTY_ID - 1, &property) ||
            !parse_unsigned(argv[6], 100, 30000, &timeout_ms)) {
            fprintf(stderr,
                "Usage: %s --read-property DEVICE_ID OBJECT_TYPE OBJECT_INSTANCE PROPERTY TIMEOUT_MS\n",
                argv[0]);
            return 64;
        }
        return read_property_transaction(
            (uint32_t)device_id, (BACNET_OBJECT_TYPE)object_type,
            (uint32_t)object_instance, (BACNET_PROPERTY_ID)property,
            (unsigned)timeout_ms);
    }
    fprintf(stderr,
        "Usage: %s [--discover-ms 100..30000] | "
        "--read-property DEVICE_ID OBJECT_TYPE OBJECT_INSTANCE PROPERTY TIMEOUT_MS\n",
        argv[0]);
    return 64;
}
