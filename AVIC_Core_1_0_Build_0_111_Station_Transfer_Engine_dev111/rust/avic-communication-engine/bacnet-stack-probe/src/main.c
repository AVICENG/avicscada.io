#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "bacnet/bacdef.h"
#include "bacnet/bacdcode.h"
#include "bacnet/bactext.h"
#include "bacnet/iam.h"
#include "bacnet/version.h"

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

    printf("bacnet_iam_codec=ok device=%u max_apdu=%u segmentation=%d vendor=%u truncated_payloads_rejected=%d wrong_object_rejected=1\n",
           (unsigned)device, max_apdu, segmentation, (unsigned)vendor, length);
    return 0;
}

int main(void)
{
    const char *device_object = bactext_object_type_name(OBJECT_DEVICE);
    if (device_object == NULL) {
        return 2;
    }
    if (iam_codec_self_test() != 0) {
        return 3;
    }
    printf("AVIC BACnet Stack C probe: %s; object=%s; codec=self-test-passed\n",
           BACNET_VERSION_TEXT, device_object);
    return 0;
}
