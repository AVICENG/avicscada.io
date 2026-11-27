#include <stdio.h>
#include "bacnet/bacdef.h"
#include "bacnet/bactext.h"
#include "bacnet/version.h"

int main(void)
{
    const char *device_object = bactext_object_type_name(OBJECT_DEVICE);
    if (device_object == NULL) {
        return 2;
    }
    printf("AVIC BACnet Stack POC: %s; object=%s\n",
           BACNET_VERSION_TEXT, device_object);
    return 0;
}
