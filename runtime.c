// runtime.c
// The Native WebGPU/Graphics Runtime Mock for Myo Language

// NOTE: No standard headers (<stdio.h> or <stdlib.h>) are included.
// This supports standalone Clang installations without Visual Studio / Windows SDKs.

#ifdef __cplusplus
extern "C" {
#endif
    int printf(const char* format, ...);
    void exit(int status); // Declared for safe execution termination in freestanding mode
    int rand(void);        // Exported from msvcrt.dll for random coordinates

    // GCC/MinGW targets require __main to run global constructors/destructors.
    // Under -nostdlib freestanding compiles, we must provide a dummy implementation.
    void __main(void) {}

    // --- Win32 Native Raw Declarations (Freestanding Windows GUI Setup) ---
    typedef void* HANDLE;
    typedef void* HWND;
    typedef void* HINSTANCE;
    typedef void* HDC;
    typedef void* HBRUSH;
    typedef void* HMENU;
    typedef void* HICON;
    typedef void* HCURS;
    typedef void* HGDIOBJ;
    typedef unsigned int UINT;
    typedef unsigned long DWORD;
    typedef long long LRESULT;
    typedef unsigned long long WPARAM;
    typedef long long LPARAM;
    typedef unsigned long COLORREF;

    typedef struct tagWNDCLASSEXA {
        UINT      cbSize;
        UINT      style;
        LRESULT (*lpfnWndProc)(HWND, UINT, WPARAM, LPARAM);
        int       cbClsExtra;
        int       cbWndExtra;
        HINSTANCE hInstance;
        HICON     hIcon;
        HCURS     hCursor;
        HBRUSH    hbrBackground;
        const char* lpszMenuName;
        const char* lpszClassName;
        HICON     hIconSm;
    } WNDCLASSEXA;

    typedef struct tagPOINT {
        long x;
        long y;
    } POINT;

    typedef struct tagMSG {
        HWND   hwnd;
        UINT   message;
        WPARAM wParam;
        LPARAM lParam;
        DWORD  time;
        POINT  pt;
        DWORD  lPrivate;
    } MSG;

    typedef struct tagRECT {
        long left;
        long top;
        long right;
        long bottom;
    } RECT;

    // Win32 Constants
    #define CS_HREDRAW 0x0002
    #define CS_VREDRAW 0x0001
    #define WS_OVERLAPPEDWINDOW 0x00CF0000L
    #define CW_USEDEFAULT ((int)0x80000000)
    #define SW_SHOW 5
    #define WM_DESTROY 0x0002
    #define WM_CLOSE 0x0010
    #define PM_REMOVE 0x0001
    #define RGB(r,g,b) ((COLORREF)(((unsigned char)(r)|((unsigned short)((unsigned char)(g))<<8))|(((DWORD)(unsigned char)(b))<<16)))

    // Win32 API functions loaded from user32.dll and gdi32.dll
    __declspec(dllimport) LRESULT DefWindowProcA(HWND hWnd, UINT Msg, WPARAM wParam, LPARAM lParam);
    __declspec(dllimport) unsigned short RegisterClassExA(const WNDCLASSEXA*);
    __declspec(dllimport) HWND CreateWindowExA(DWORD dwExStyle, const char* lpClassName, const char* lpWindowName, DWORD dwStyle, int X, int Y, int nWidth, int nHeight, HWND hWndParent, HMENU hMenu, HINSTANCE hInstance, void* lpParam);
    __declspec(dllimport) int ShowWindow(HWND hWnd, int nCmdShow);
    __declspec(dllimport) int UpdateWindow(HWND hWnd);
    __declspec(dllimport) int PeekMessageA(MSG* lpMsg, HWND hWnd, UINT wMsgFilterMin, UINT wMsgFilterMax, UINT wRemoveMsg);
    __declspec(dllimport) int TranslateMessage(const MSG* lpMsg);
    __declspec(dllimport) LRESULT DispatchMessageA(const MSG* lpMsg);
    __declspec(dllimport) void PostQuitMessage(int nExitCode);
    __declspec(dllimport) HBRUSH GetStockObject(int fnObject);
    __declspec(dllimport) short GetAsyncKeyState(int vKey);

    // GDI Rendering Engine Functions
    __declspec(dllimport) HDC GetDC(HWND hWnd);
    __declspec(dllimport) int ReleaseDC(HWND hWnd, HDC hDC);
    __declspec(dllimport) HDC CreateCompatibleDC(HDC hdc);
    __declspec(dllimport) void* CreateCompatibleBitmap(HDC hdc, int cx, int cy);
    __declspec(dllimport) HGDIOBJ SelectObject(HDC hdc, HGDIOBJ h);
    __declspec(dllimport) int BitBlt(HDC hdcDest, int xDest, int yDest, int w, int h, HDC hdcSrc, int xSrc, int ySrc, DWORD rop);
    __declspec(dllimport) int DeleteDC(HDC hdc);
    __declspec(dllimport) int DeleteObject(HGDIOBJ ho);
    __declspec(dllimport) HBRUSH CreateSolidBrush(COLORREF crColor);
    __declspec(dllimport) int FillRect(HDC hDC, const RECT* lprc, HBRUSH hbr);
    __declspec(dllimport) DWORD SetTextColor(HDC hdc, DWORD color);
    __declspec(dllimport) int SetBkMode(HDC hdc, int mode);
    __declspec(dllimport) int TextOutA(HDC hdc, int x, int y, const char* lpString, int c);
#ifdef __cplusplus
}
#endif

// Shared memory graphics handle for the current backbuffer frame
static HDC hdcMemGlobal = (HDC)0;

// Game state lifecycle endpoints compiled directly from the Myo source code
extern void main_game_init();
extern void main_game_loop(); 

// Custom Windows Procedure to handle OS window events
LRESULT WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
        case WM_CLOSE:
        case WM_DESTROY:
            printf("[Myo Engine] Window Closed. Shutting down system...\n");
            PostQuitMessage(0);
            return 0;
    }
    return DefWindowProcA(hwnd, uMsg, wParam, lParam);
}

// --- HARDWARE INTERACTION RUNTIME API BINDINGS EXPOSED TO LLVM ---

// myo_clear(r, g, b)
void myo_clear(float r, float g, float b) {
    if (hdcMemGlobal) {
        RECT bgRect = {0, 0, 1280, 720};
        HBRUSH hBgBrush = CreateSolidBrush(RGB((int)r, (int)g, (int)b));
        FillRect(hdcMemGlobal, &bgRect, hBgBrush);
        DeleteObject(hBgBrush);
    }
}

// myo_draw_rect(x, y, w, h, r, g, b)
void myo_draw_rect(float x, float y, float w, float h, float r, float g, float b) {
    if (hdcMemGlobal) {
        HBRUSH hBrush = CreateSolidBrush(RGB((int)r, (int)g, (int)b));
        RECT rect = {(long)x, (long)y, (long)(x + w), (long)(y + h)};
        FillRect(hdcMemGlobal, &rect, hBrush);
        DeleteObject(hBrush);
    }
}

// myo_draw_circle(cx, cy, radius, r, g, b)
void myo_draw_circle(float cx, float cy, float radius, float r, float g, float b) {
    if (hdcMemGlobal) {
        HBRUSH hBrush = CreateSolidBrush(RGB((int)r, (int)g, (int)b));
        // Approximate a circle with an offset square in core GDI
        RECT rect = {(long)(cx - radius), (long)(cy - radius), (long)(cx + radius), (long)(cy + radius)};
        FillRect(hdcMemGlobal, &rect, hBrush);
        DeleteObject(hBrush);
    }
}

// myo_draw_score(score, x, y)
void myo_draw_score(float score, float x, float y) {
    if (hdcMemGlobal) {
        SetTextColor(hdcMemGlobal, RGB(255, 255, 255));
        SetBkMode(hdcMemGlobal, 1); // Transparent mode

        char scoreHUD[32];
        int scoreInt = (int)score;
        scoreHUD[0] = 'M'; scoreHUD[1] = 'Y'; scoreHUD[2] = 'O'; scoreHUD[3] = ' '; 
        scoreHUD[4] = 'S'; scoreHUD[5] = 'C'; scoreHUD[6] = 'O'; scoreHUD[7] = 'R'; 
        scoreHUD[8] = 'E'; scoreHUD[9] = ':'; scoreHUD[10] = ' ';

        int temp = scoreInt;
        int len = 0;
        if (temp == 0) {
            scoreHUD[11] = '0';
            scoreHUD[12] = '\0';
            len = 1;
        } else {
            char digits[10];
            while (temp > 0 && len < 10) {
                digits[len++] = '0' + (temp % 10);
                temp /= 10;
            }
            for (int i = 0; i < len; i++) {
                scoreHUD[11 + i] = digits[len - 1 - i];
            }
            scoreHUD[11 + len] = '\0';
        }
        TextOutA(hdcMemGlobal, (int)x, (int)y, scoreHUD, 11 + len);
    }
}

// myo_is_key_down(vk_code)
float myo_is_key_down(float vk_code) {
    short state = GetAsyncKeyState((int)vk_code);
    return (state & 0x8000) ? 1.0f : 0.0f;
}

// myo_rand(low, high)
float myo_rand(float low, float high) {
    int r = rand();
    float range = high - low;
    return low + ((float)r / 32767.0f) * range;
}

// Stubs for texture loadings in native mode
float myo_load_texture(char* filepath) { return 1.0f; }
void myo_render(float texture_id, float x, float y) {}
void myo_print_num(float val) { printf("%f\n", val); }

#ifndef MYO_NO_MAIN
int main() {
    printf("=== MYO ENGINE INITIALIZING WINDOW ===\n");

    HINSTANCE hInstance = (HINSTANCE)0; 

    // 1. Register the native Window Class
    WNDCLASSEXA wc = {0};
    wc.cbSize = sizeof(WNDCLASSEXA);
    wc.style = CS_HREDRAW | CS_VREDRAW;
    wc.lpfnWndProc = WindowProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = "MyoEngineWindowClass";
    wc.hbrBackground = (HBRUSH)(void*)(4 + 1); 

    if (!RegisterClassExA(&wc)) {
        printf("[!] Failed to register Window Class.\n");
        exit(1);
    }

    // 2. Open a fully functioning 1280x720 OS window
    HWND hwnd = CreateWindowExA(
        0,
        "MyoEngineWindowClass",
        "Myo Engine Alpha - Standalone Active Game Viewport",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, 1280, 720,
        (HWND)0, (HMENU)0, hInstance, (void*)0
    );

    if (!hwnd) {
        printf("[!] Failed to create OS Window Viewport.\n");
        exit(1);
    }

    ShowWindow(hwnd, SW_SHOW);
    UpdateWindow(hwnd);
    printf("[Myo Engine] Active Desktop Viewport Initialized Successfully.\n");

    // 3. Setup GDI double buffering systems
    HDC hdcWindow = GetDC(hwnd);
    HDC hdcMem = CreateCompatibleDC(hdcWindow);
    void* hbmMem = CreateCompatibleBitmap(hdcWindow, 1280, 720);
    SelectObject(hdcMem, hbmMem);
    hdcMemGlobal = hdcMem;

    // 4. Initialize Myo-compiled Game States (Runs 'create' method)
    main_game_init();

    // 5. Real-time Game Rendering Loop
    MSG msg = {0};
    int running = 1;

    while (running) {
        // Handle window events immediately
        while (PeekMessageA(&msg, (HWND)0, 0, 0, PM_REMOVE)) {
            if (msg.message == 0x0012) { // WM_QUIT
                running = 0;
                break;
            }
            TranslateMessage(&msg);
            DispatchMessageA(&msg);
        }

        if (!running) break;

        // Run Compiled Myo Custom Frame Code (Runs 'update' method to process game state and render elements)
        main_game_loop();

        // Flip Backbuffer directly onto Screen DC (Smooth, flicker-free presentation)
        HDC hdcScreen = GetDC(hwnd);
        BitBlt(hdcScreen, 0, 0, 1280, 720, hdcMem, 0, 0, 0x00CC0020); // SRCCOPY
        ReleaseDC(hwnd, hdcScreen);

        // Throttle frame processing loosely to ~60 FPS
        for (volatile int i = 0; i < 1800000; i++); 
    }

    // Clean GDI Objects
    DeleteDC(hdcMem);
    DeleteObject(hbmMem);
    ReleaseDC(hwnd, hdcWindow);

    printf("=== MYO ENGINE SHUTDOWN ===\n");
    exit(0);
    return 0;
}
#endif