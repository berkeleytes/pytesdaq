#include <iostream>
#include <string>
#include <limits>
#include "magsv.h"
#include "utils/squid_control_helpers.cpp"

using namespace std;

int main(int argc, char** argv) {

    // Check arguments
    unsigned short containers[3] = {(unsigned short) USHRT_MAX, (unsigned short) USHRT_MAX, (unsigned short) USHRT_MAX};
    const char* extra_args[1] = {};
    validate_args(containers, argc, argv, "get_preamp_input_voltage.exe", 0, extra_args);
    if (containers[0] == (unsigned short) USHRT_MAX) {
        return 1; }
    unsigned short channel = containers[0];
    unsigned short error = containers[2];

    // Get V - Vb
    double V_Vb = 0;
    MA_read_V_Vb(channel, &error, &V_Vb);
    errorout(error);

    cout << "V - Vb = " << V_Vb << " uV" << endl;
    cout << flush;

    // Close connection
    MA_closeUSB(&error);
    errorout(error);

    return 0;
}
