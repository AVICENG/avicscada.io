#include <stdio.h>
#include "bacnet/version.h"

int main(void)
{
    printf("AVIC BACnet Stack POC build probe: %s\n", BACNET_VERSION_TEXT);
    return 0;
}
