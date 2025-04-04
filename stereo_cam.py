import cv2
import os

def get_stereo_camera():
    max_index = 3
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame.shape[1] == 2560:
                return cap
    return None

def main():
    # 저장할 디렉토리 생성 (없으면 생성)
    capture_dir = "./capture"
    if not os.path.exists(capture_dir):
        os.makedirs(capture_dir)

    stereo_camera = get_stereo_camera()
    if stereo_camera is None:
        print("Stereo camera를 찾을 수 없습니다.")
        return

    # stereo camera 열기 (기본 장치번호 0 사용)
    cap = stereo_camera
    if not cap.isOpened():
        print("카메라를 열 수 없습니다.")
        return

    print("엔터키를 눌러 캡처하세요...")
    i = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("프레임을 가져올 수 없습니다.")
            break
        
        cv2.imshow("Stereo Camera", frame)
        
        # 1ms 대기 후 키 입력 확인 (엔터키: 13)
        key = cv2.waitKey(1)
        if key == 13:  # 엔터키를 누르면
            # 전체 이미지 저장
            full_img_path = os.path.join(capture_dir, f"{i:03d}.png")
            cv2.imwrite(full_img_path, frame)
            print("저장됨:", full_img_path)
            
            # 프레임을 좌우로 분할 (가로 기준 중앙에서 나눔)
            height, width, _ = frame.shape
            half_width = width // 2
            left_img = frame[:, :half_width]
            right_img = frame[:, half_width:]
            
            left_img_path = os.path.join(capture_dir, f"{i:03d}_L.png")
            right_img_path = os.path.join(capture_dir, f"{i:03d}_R.png")
            
            cv2.imwrite(left_img_path, left_img)
            cv2.imwrite(right_img_path, right_img)
            
            print("좌측 이미지 저장됨:", left_img_path)
            print("우측 이미지 저장됨:", right_img_path)
            i += 1
            

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
