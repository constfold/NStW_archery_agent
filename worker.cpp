/**
 * Only for `Sidequest_ArcheryRange_TargetManager.gm` script.
 * 
 * The memory layout of the GameMonkey version used by the game is different from the original version.
 * Which is why we define structs/functions by ourselves.
*/
#define _CRT_SECURE_NO_WARNINGS
#include "detours.h"

#include <format>
#include <fstream>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <atomic>

template<typename... Args>
void dprint(std::string_view rt_fmt_str, Args&&... args)
{
    std::string s = std::vformat(rt_fmt_str, std::make_format_args(args...));

    OutputDebugStringA(s.c_str());
}

typedef void (*gmMachineLib_t)(void* machine);
typedef void (*RegisterLibrary_t)(void* a_machine, void* a_functions, int a_numFunctions, const char* a_asTable, bool a_newTable);
typedef INT64 (*ExecuteGmLib_t)(void* self, char* filename, char* fullname, char* buf, unsigned int buflen, void* a6, char a7);

ExecuteGmLib_t ExecuteGmLib_o = (ExecuteGmLib_t)(0x1401A4000);
gmMachineLib_t gmMachineLib_o = (gmMachineLib_t)(0x14014DCD0);
RegisterLibrary_t RegisterLibrary_o = (RegisterLibrary_t)(0x140137F20);

struct gmFunctionEntry
{
    const char* m_name;
    int(*m_function)(INT64);
    const void* m_userData;
};

struct gmVariable {
    union {
        int m_int;
        float m_float;
        UINT64 m_ptr;
        UINT64 m_large[2];
    } m_value;
    UINT64 m_type;
};

struct KeyboardEvent {
    char key;
    int delay;
    int release;
};

std::queue<KeyboardEvent> dataQueue;
std::mutex mtx;
std::condition_variable cv;
std::atomic_bool cancel;

DWORD WINAPI SendInputWorker(LPVOID lpParam)
{
    while (1) {
        dprint("[Executor] Wait Incoming Events");
        std::unique_lock<std::mutex> lock(mtx);
        cv.wait(lock, [] { return !dataQueue.empty() || cancel; });

        if (cancel) {
            while (!dataQueue.empty()) dataQueue.pop();
            cancel = false;
            continue;
        }
        while (!dataQueue.empty()) {
            auto data = dataQueue.front();
            dataQueue.pop();

            lock.unlock();

            INPUT input = { 0 };
            input.type = INPUT_KEYBOARD;
            input.ki.wVk = 0;
            input.ki.wScan = data.key;
            input.ki.dwFlags = KEYEVENTF_SCANCODE;
            if (data.release) {
                dprint("[Executor] [{}] Send Release {} Event", GetTickCount(), data.key);
                input.ki.dwFlags |= KEYEVENTF_KEYUP;
            }
            else {
                dprint("[Executor] [{}] Send Press {} Event", GetTickCount(), data.key);
            }
            if (!SendInput(1, &input, sizeof(INPUT))) {
                dprint("[Executor] SendInput Error = {}", GetLastError());
            }
            Sleep(data.delay);

            lock.lock();
        }
    }

    return 0;
}

int __cdecl gmInput(INT64 a_thread) {
    auto paramsNum = *(short*)(a_thread + 0xA0);
    auto m_stack = *(gmVariable**)(a_thread + 0x38);
    auto m_base = *(int*)(a_thread + 0x48);
    auto arg1 = (m_stack + m_base)->m_value.m_int;
    auto arg2 = (m_stack + m_base + 1)->m_value.m_float;
    auto arg3 = (m_stack + m_base + 2)->m_value.m_int;


    std::lock_guard<std::mutex> lock(mtx);
    dataQueue.push(KeyboardEvent{ .key = (char)arg1, .delay = (int)arg2, .release = arg3 });
    cv.notify_one();
    dprint("[Executor] arg1={}, arg2={}, arg3={}, (int)arg2={}", arg1, arg2, arg3, (int)arg2);

    return 0;
}

int gmCancel(INT64 a_thread) {
    cancel = true;
    cv.notify_one();
    return 0;
}

gmFunctionEntry s_myLibrary[] =
{
    { "Dinput", gmInput },
    { "Dcancel", gmCancel }
};

void gmMachineLib_detour(void* machine) {
    dprint("[Executor] RegisterLibrary");
    gmMachineLib_o(machine);

    dprint("[Executor] Create Worker Thread");
    if (!CreateThread(NULL, 0, SendInputWorker, NULL, 0, NULL)) {
        dprint("[Executor] CreateThread Error={}", GetLastError());
    }
    RegisterLibrary_o(machine, s_myLibrary, sizeof(s_myLibrary) / sizeof(s_myLibrary[0]), NULL, 1);
}

INT64 ExecuteGmLib_detour(void* self, char* filename, char* fullname, char* buf, unsigned int buflen, void* a6, char a7) {
    dprint("[Executor] ExecuteGmLib_detour {}", filename);
    if (!strcmp(filename, "Sidequest_ArcheryRange_TargetManager.gm")) {
        std::ifstream file("patch_.gmb", std::ios::binary | std::ios::ate);
        std::streamsize size = file.tellg();
        file.seekg(0, std::ios::beg);

        auto buf2 = (char*)malloc(size);// same allocator
        file.read(buf2, size);

        buf = buf2;
        buflen = size;
        dprint("[Executor] fake buf=0x{:X} len={}", (UINT64)buf2, buflen);
    }
    return ExecuteGmLib_o(self, filename, fullname, buf, buflen, a6, a7);
}

void Init() {
    dprint("[Executor] Begin Init");

    DetourTransactionBegin();
    DetourUpdateThread(GetCurrentThread());
    DetourAttach(&ExecuteGmLib_o, ExecuteGmLib_detour);
    DetourAttach(&gmMachineLib_o, gmMachineLib_detour);
    auto errorCode = DetourTransactionCommit();

    dprint("[Executor] Detour error code: {:X}", errorCode);
    
}


BOOL APIENTRY DllMain( HMODULE hModule,
                       DWORD  ul_reason_for_call,
                       LPVOID lpReserved
                     )
{
    switch (ul_reason_for_call)
    {
    case DLL_PROCESS_ATTACH:
        DetourRestoreAfterWith();
        DisableThreadLibraryCalls(hModule);
        Init();
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
    case DLL_PROCESS_DETACH:
        break;
    }
    return TRUE;
}

