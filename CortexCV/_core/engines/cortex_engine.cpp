// cortex_engine.cpp
#include <mfapi.h>
#include <mfidl.h>
#include <mfreadwrite.h>
#include <mfobjects.h>
#include <mferror.h>
#include <wrl/client.h>
#include <iostream>
#include <string>       // For std::string and related functions
#include <locale>       // For std::wstring_convert and std::codecvt_utf8
#include <codecvt>      // For std::wstring_convert and std::codecvt_utf8

using namespace Microsoft::WRL;

#pragma comment(lib, "mfplat.lib")
#pragma comment(lib, "mfreadwrite.lib")
#pragma comment(lib, "mfuuid.lib")
#pragma comment(lib, "mf.lib")
#pragma comment(lib, "ole32.lib")

extern "C" {
    __declspec(dllexport) int start_camera();
    __declspec(dllexport) int stop_camera();
    __declspec(dllexport) unsigned char* get_frame();
    __declspec(dllexport) int get_width();
    __declspec(dllexport) int get_height();
    __declspec(dllexport) const char* get_format();
    __declspec(dllexport) int get_stride();
    __declspec(dllexport) int get_frame_length();
}

// Globals
IMFSourceReader* g_pReader = nullptr;
IMFSourceReader* pReader = nullptr;
DWORD width = 0, height = 0;
unsigned char* frameBuffer = nullptr;
LONG stride = 0;
const char* formatName = "RGB32";  // Fixed format

std::wstring GUIDtoWString(const GUID& guid) {
    wchar_t buffer[64];
    swprintf_s(buffer, 64,
        L"{%08lX-%04hX-%04hX-%02hhX%02hhX-%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX}",
        guid.Data1, guid.Data2, guid.Data3,
        guid.Data4[0], guid.Data4[1], guid.Data4[2], guid.Data4[3],
        guid.Data4[4], guid.Data4[5], guid.Data4[6], guid.Data4[7]);
    return std::wstring(buffer);
}

int start_camera() {
    CoInitializeEx(nullptr, COINIT_MULTITHREADED);

    HRESULT hr = MFStartup(MF_VERSION);
    if (FAILED(hr)) {
        std::wcerr << L"MFStartup failed: 0x" << std::hex << hr << std::endl;
        return false;
    }

    ComPtr<IMFAttributes> pConfig;
    hr = MFCreateAttributes(&pConfig, 1);
    if (FAILED(hr)) return false;

    hr = pConfig->SetGUID(MF_DEVSOURCE_ATTRIBUTE_SOURCE_TYPE, MF_DEVSOURCE_ATTRIBUTE_SOURCE_TYPE_VIDCAP_GUID);
    if (FAILED(hr)) return false;

    IMFActivate** ppDevices = nullptr;
    UINT32 count = 0;

    hr = MFEnumDeviceSources(pConfig.Get(), &ppDevices, &count);
    if (FAILED(hr) || count == 0) {
        std::wcerr << L"No video capture devices found." << std::endl;
        return false;
    }

    ComPtr<IMFMediaSource> pSource;
    hr = ppDevices[0]->ActivateObject(IID_PPV_ARGS(&pSource));
    for (UINT32 i = 0; i < count; ++i) ppDevices[i]->Release();
    CoTaskMemFree(ppDevices);

    if (FAILED(hr)) {
        std::wcerr << L"Failed to activate camera source." << std::endl;
        return false;
    }

    hr = MFCreateSourceReaderFromMediaSource(pSource.Get(), nullptr, &g_pReader);
    if (FAILED(hr)) {
        std::wcerr << L"Failed to create source reader." << std::endl;
        return false;
    }

    IMFMediaType* pType = nullptr;
    bool selected = false;
    int i = 0;

    // Prioritize MJPG
    while (SUCCEEDED(g_pReader->GetNativeMediaType(MF_SOURCE_READER_FIRST_VIDEO_STREAM, i++, &pType))) {
        GUID subtype;
        if (SUCCEEDED(pType->GetGUID(MF_MT_SUBTYPE, &subtype))) {
            std::wcout << L"Found subtype: " << GUIDtoWString(subtype) << std::endl;
            if (subtype == MFVideoFormat_MJPG) {
                hr = g_pReader->SetCurrentMediaType(MF_SOURCE_READER_FIRST_VIDEO_STREAM, nullptr, pType);
                if (SUCCEEDED(hr)) {
                    std::wcout << L"Selected preferred subtype: MJPG" << std::endl;
                    formatName = "MJPG";
                    selected = true;
                    pType->Release();
                    break;
                }
            }
        }
        pType->Release();
    }

    if (!selected) {
        i = 0;
        while (SUCCEEDED(g_pReader->GetNativeMediaType(MF_SOURCE_READER_FIRST_VIDEO_STREAM, i++, &pType))) {
            GUID subtype;
            if (SUCCEEDED(pType->GetGUID(MF_MT_SUBTYPE, &subtype))) {
                std::wcout << L"Found subtype: " << GUIDtoWString(subtype) << std::endl;
                if (subtype == MFVideoFormat_RGB32) {
                    hr = g_pReader->SetCurrentMediaType(MF_SOURCE_READER_FIRST_VIDEO_STREAM, nullptr, pType);
                    if (SUCCEEDED(hr)) {
                        std::wcout << L"Selected fallback subtype: RGB32" << std::endl;
                        formatName = "RGB32";
                        selected = true;
                        pType->Release();
                        break;
                    }
                }
            }
            pType->Release();
        }
    }

    if (!selected) {
        i = 0;
        UINT32 width_local = 0, height_local = 0;
        IMFMediaType* pCurrentType = nullptr;
        HRESULT hr_get_type = g_pReader->GetCurrentMediaType(MF_SOURCE_READER_FIRST_VIDEO_STREAM, &pCurrentType);
        if (SUCCEEDED(hr_get_type) && pCurrentType) {
            HRESULT hr_get_size = MFGetAttributeSize(pCurrentType, MF_MT_FRAME_SIZE, &width_local, &height_local);
            if (SUCCEEDED(hr_get_size)) {
                width = width_local;
                height = height_local;
                std::wcout << L"Camera resolution: " << width << L"x" << height << std::endl;
            } else {
                std::wcerr << L"Failed to get frame size after setting format. Error: 0x" << std::hex << hr_get_size << std::endl;
                width = 0;
                height = 0;
            }
            pCurrentType->Release();
        } else {
            std::wcerr << L"Failed to get current media type after setting format. Error: 0x" << std::hex << hr_get_type << std::endl;
            width = 0;
            height = 0;
        }
    }
    if (strcmp(formatName, "MJPG") == 0) {
        // For MJPG, the buffer size will vary per frame. You might need to handle this differently.
        frameBuffer = new (std::nothrow) unsigned char[1024 * 768 * 4]; // A large enough initial size
        stride = 0; // Stride doesn't apply directly to compressed formats
    } else {
        frameBuffer = new (std::nothrow) unsigned char[width * height * 4]; // Assuming RGB or similar
        stride = width * 4;
    }

    stride = width * 4;
    pReader = g_pReader;  // Fix for get_frame()

    return 0;
}

int stop_camera() {
    if (pReader) {
        pReader->Release();
        pReader = nullptr;
        pReader = nullptr;
    }

    MFShutdown();
    CoUninitialize();

    delete[] formatName;
    formatName = nullptr;
    return 0;
}

DWORD lastFrameLength = 0;

unsigned char* get_frame() {
    if (!pReader) return nullptr;

    IMFSample* pSample = nullptr;
    DWORD flags = 0;
    HRESULT hr = pReader->ReadSample(
        MF_SOURCE_READER_FIRST_VIDEO_STREAM, 0, nullptr, &flags, nullptr, &pSample
    );

    if (FAILED(hr) || !pSample) return nullptr;

    IMFMediaBuffer* pBuffer = nullptr;
    hr = pSample->ConvertToContiguousBuffer(&pBuffer);
    if (FAILED(hr)) {
        pSample->Release();
        return nullptr;
    }

    BYTE* pData = nullptr;
    DWORD maxLength = 0, currentLength = 0;
    pBuffer->Lock(&pData, &maxLength, &currentLength);
    memcpy(frameBuffer, pData, currentLength);
    pBuffer->Unlock();

    pBuffer->Release();
    pSample->Release();

    lastFrameLength = currentLength; // Store the length of the last frame

    return frameBuffer;
}

int get_frame_length() {
    return static_cast<int>(lastFrameLength);
}


int get_width() {
    return static_cast<int>(width);
}

int get_height() {
    return static_cast<int>(height);
}

const char* get_format() {
    return formatName;
}

int get_stride() {
    return static_cast<int>(stride);
}
