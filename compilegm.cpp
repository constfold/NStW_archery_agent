
/**
 * Compile a GameMonkey script to a GameMonkey bytecode file.
 * 
 * Note: The game uses a modified version of GameMonkey, so make sure to patch the original
 * GameMonkey source code before compiling.
 * */
#include "gmmachine.h"
#include "gmStreamBuffer.h"

#include <iostream>
#include <fstream>
#include <sstream>
#include <filesystem>
#include <vector>

int main()
{
    gmMachine gm;
    gm.SetDebugMode(true);

    std::ifstream f("patch.gm");
    std::stringstream buffer;
    buffer << f.rdbuf();

    std::cout << buffer.str() << std::endl;

    gmStreamBufferDynamic gms{};
    auto errors = gm.CompileStringToLib(buffer.str().c_str(), gms);
    if (errors != 0) {
        bool first = true;
        const char* message;

        while ((message = gm.GetLog().GetEntry(first)))
        {
            std::cout << message << std::endl;
        }
        gm.GetLog().Reset();
    }

    std::ofstream fo("patch.gmb", std::ios::out | std::ios::binary);
    fo.write(gms.GetData(), gms.GetSize());
    fo.close();
}
