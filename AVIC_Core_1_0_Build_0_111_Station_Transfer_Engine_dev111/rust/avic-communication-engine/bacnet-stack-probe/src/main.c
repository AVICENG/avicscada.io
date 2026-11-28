#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include <stdlib.h>

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

int main(int argc, char **argv)
{
    const char *device_object = bactext_object_type_name(OBJECT_DEVICE);
    if (device_object == NULL) {
        return 2;
    }
    if (iam_codec_self_test() != 0) {
        return 3;
    }
    if (read_property_codec_self_test() != 0) {
        return 4;
    }
    printf("AVIC BACnet Stack C probe: %s; object=%s; codec=self-test-passed\\n",
           BACNET_VERSION_TEXT, device_object);

    if (argc == 1) {
        return 0;
    }
    if (argc != 3 || strcmp(argv[1], "--discover-ms") != 0) {
        fprintf(stderr, "Usage: %s [--discover-ms 100..30000]\\n", argv[0]);
        return 64;
    }
    char *end = NULL;
    unsigned long timeout_ms = strtoul(argv[2], &end, 10);
    if (!end || *end != '\0' || timeout_ms < 100 || timeout_ms > 30000) {
        fprintf(stderr, "Discovery timeout must be 100..30000 ms\\n");
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
    mstimer_set(&deadline, timeout_ms);
    mstimer_set(&maintenance, 1000);
    Send_WhoIs_To_Network(&destination, -1, -1);

    while (!mstimer_expired(&deadline)) {
        uint16_t received = datalink_receive(
            &source, rx_buffer, MAX_MPDU, 100u);
        if (received > 0) {
            npdu_handler(&source, rx_buffer, received);
        }
        if (mstimer_expired(&maintenance)) {
            datalink_maintenance_timer(1u);
            mstimer_reset(&maintenance);
        }
    }

    unsigned count = address_count();
    printf("bacnet_discovery=complete timeout_ms=%lu devices=%u\\n",
           timeout_ms, count);
    for (unsigned index = 0; index < count; ++index) {
        uint32_t device_id = 0;
        unsigned max_apdu = 0;
        BACNET_ADDRESS address = { 0 };
        if (address_get_by_index(index, &device_id, &max_apdu, &address)) {
            printf("device_id=%u max_apdu=%u mac_len=%u network=%u\\n",
                   (unsigned)device_id, max_apdu,
                   (unsigned)address.mac_len, (unsigned)address.net);
        }
    }
    datalink_cleanup();
    return 0;
}
