
#include <stdio.h>
#include <stdlib.h>
#include <opencv2/opencv.hpp>

using namespace cv;

extern "C" {
    __declspec(dllexport) int start_camera();
    __declspec(dllexport) int stop_camera();
    __declspec(dllexport) unsigned char* get_frame();
    __declspec(dllexport) int get_width();
    __declspec(dllexport) int get_height();
}

// Global vars
VideoCapture cap;
Mat frame;

int start_camera() {
    cap.open(0);
    if (!cap.isOpened()) return -1;
    return 0;
}

int stop_camera() {
    cap.release();
    return 0;
}

unsigned char* get_frame() {
    cap >> frame;
    if (frame.empty()) return NULL;
    return frame.data;
}

int get_width() {
    return frame.cols;
}

int get_height() {
    return frame.rows;
}
