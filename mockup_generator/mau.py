# Ngân hàng mẫu cho kỳ thi giả lập. Ứng dụng không import file này.

SUBJECTS = [
    ("CSDL", "Cơ sở dữ liệu", 3, "Khoa Công nghệ thông tin"),
    ("KDL", "Kho dữ liệu", 3, "Khoa Công nghệ thông tin"),
    ("PYT", "Lập trình Python", 3, "Khoa Công nghệ thông tin"),
    ("MMT", "Mạng máy tính", 3, "Khoa Viễn thông"),
    ("XSTK", "Xác suất thống kê", 2, "Khoa Cơ bản"),
    ("AVCN", "Tiếng Anh chuyên ngành", 2, "Khoa Cơ bản"),
]

# ma, họ tên, ngày sinh, lớp gốc, lớp hiện tại, trạng thái, vai trò
PEOPLE = [
    ("B23DCKD004", "Nguyễn Quý Tường Anh", "2005-03-12", "D23CQKD03", "D23CQCN01", "DANG_HOC", "thanh_vien"),
    ("B23DCKD008", "Tạ Hoà Bình", "2005-07-02", "D23CQKD03", "D23CQKD03", "DANG_HOC", "thanh_vien"),
    ("B23DCKD014", "Nguyễn Tiến Đạt", "2005-01-19", "D23CQKD03", "D23CQKD03", "DANG_HOC", "thanh_vien"),
    ("B23DCKD030", "Mai Quốc Hưng", "2005-11-08", "D23CQKD03", "D23CQKD03", "DANG_HOC", "thanh_vien"),
    ("HS-BL01", "Phạm Thu Hà", "2005-04-21", "D23CQKD03", "D23CQKD03", "BAO_LUU", "bao_luu"),
    ("HS-CB01", "Lê Minh Khoa", "2005-08-30", "D23CQCN01", "D23CQCN01", "CANH_BAO_HOC_VU", "canh_bao"),
    ("HS-CC01", "Đỗ Gia Hân", "2005-02-14", "D23CQKT02", "D23CQKT02", "DANG_HOC", "chi_hoc"),
    ("HS-THI01", "Vũ Nhật Nam", "2005-06-09", "D23CQVT04", "D23CQVT04", "DANG_HOC", "chi_thi"),
]

CLASSES = ["D23CQCN01", "D23CQKT02", "D23CQKD03", "D23CQVT04"]
ENROLL_AT = "2026-09-05 00:00:00"
SCD_AT = "2026-10-12 08:00:00"
END_OF_TIME = "9999-12-31 23:59:59"

LESSONS = [
    ("CSDL_B1", "CSDL", "Mô hình thực thể liên kết", "VIDEO", 28),
    ("CSDL_B2", "CSDL", "Chuẩn hóa và phụ thuộc hàm", "VIDEO", 34),
    ("CSDL_B3", "CSDL", "Bài đọc giao dịch và khóa", "TAI_LIEU", 20),
    ("KDL_B1", "KDL", "OLTP, OLAP và bốn đặc tính kho", "VIDEO", 30),
    ("KDL_B2", "KDL", "Mô hình chiều và mức hạt fact", "VIDEO", 36),
    ("KDL_B3", "KDL", "Đọc thêm SCD và dimension dùng chung", "TAI_LIEU", 18),
    ("PYT_B1", "PYT", "Cấu trúc list, dict, tuple", "VIDEO", 24),
    ("PYT_B2", "PYT", "Hàm, module và xử lý file", "VIDEO", 32),
    ("PYT_B3", "PYT", "Ghi chép dữ liệu với Python", "TAI_LIEU", 16),
    ("MMT_B1", "MMT", "Mô hình TCP/IP", "VIDEO", 26),
    ("MMT_B2", "MMT", "Địa chỉ IP và DNS", "VIDEO", 22),
    ("MMT_B3", "MMT", "Tài liệu giao thức HTTP", "TAI_LIEU", 15),
    ("XSTK_B1", "XSTK", "Trung bình, trung vị, phương sai", "VIDEO", 27),
    ("XSTK_B2", "XSTK", "Xác suất và biến cố độc lập", "VIDEO", 25),
    ("XSTK_B3", "XSTK", "Bảng tra và bài tập phân phối", "TAI_LIEU", 18),
    ("AVCN_B1", "AVCN", "Từ vựng dữ liệu và truy vấn", "VIDEO", 20),
    ("AVCN_B2", "AVCN", "Đọc đoạn mô tả kho dữ liệu", "VIDEO", 18),
    ("AVCN_B3", "AVCN", "Glossary thuật ngữ OLAP", "TAI_LIEU", 12),
]

# Nội dung, A, B, C, D, đáp án.
QUESTIONS = {
    "CSDL": [
        ("Khóa chính của một bảng dùng để làm gì?", "Cho phép trùng dòng", "Xác định duy nhất một dòng", "Mã hóa mật khẩu", "Thay thế mọi truy vấn", "B"),
        ("Dạng chuẩn 3NF nhằm xử lý vấn đề nào?", "Phụ thuộc bắc cầu vào khóa", "Mất kết nối mạng", "Thiếu giao diện", "Trùng tên cột", "A"),
        ("INNER JOIN trả về những dòng nào?", "Mọi dòng của bảng trái", "Tích Descartes không lọc", "Dòng khớp điều kiện nối", "Chỉ dòng không khớp", "C"),
        ("Chữ I trong ACID nghĩa là gì?", "Index", "Insert", "Identity", "Isolation", "D"),
        ("Khóa ngoại dùng để làm gì?", "Ràng buộc tham chiếu sang bảng khác", "Tăng điểm bài thi", "Xóa mọi chỉ mục", "Đổi kiểu dữ liệu cột", "A"),
    ],
    "KDL": [
        ("OLTP khác OLAP ở điểm nào?", "Hai bên dùng chung một báo cáo", "OLTP phục vụ tác nghiệp, OLAP phục vụ phân tích", "OLAP thay khóa chính", "OLTP không lưu giao dịch", "B"),
        ("SCD Type 2 lưu lịch sử bằng cách nào?", "Xóa hẳn dòng cũ", "Ghi đè thuộc tính tại chỗ", "Đóng bản ghi cũ và thêm bản ghi mới", "Chỉ lưu ở file log ngoài kho", "C"),
        ("Fact constellation là gì?", "Nhiều bảng fact dùng chung một số dimension", "Một fact không có khóa", "Chỉ một chiều thời gian", "Bảng nguồn OLTP", "A"),
        ("Grain của bảng fact là gì?", "Tên cột đo lường", "Khóa surrogate", "Ngày nạp ETL", "Mức chi tiết của một dòng fact", "D"),
        ("Unknown member (khóa -1) dùng để làm gì?", "Xóa fact lỗi", "Giữ fact khi mã chiều không tra được", "Đánh dấu học sinh giỏi", "Thay materialized view", "B"),
    ],
    "PYT": [
        ("list khác tuple ở điểm nào?", "list sửa được, tuple không sửa phần tử", "tuple chạy nhanh hơn mọi trường hợp", "list không chứa số", "tuple là câu lệnh SQL", "A"),
        ("dict trong Python truy cập chủ yếu bằng gì?", "Chỉ số âm", "Tên file", "Khóa", "Số thứ tự cột", "C"),
        ("with open(...) giúp việc gì?", "Tăng điểm chuyên cần", "Tự đóng file khi ra khỏi khối lệnh", "Biên dịch SQL", "Tạo khóa chính", "B"),
        ("range(3) sinh ra dãy nào?", "1, 2, 3", "3, 2, 1", "0, 1, 2, 3", "0, 1, 2", "D"),
        ("pip dùng để làm gì?", "Cài thư viện bên ngoài", "Vẽ sơ đồ sao", "Chấm bài trắc nghiệm", "Nén video bài giảng", "A"),
    ],
    "MMT": [
        ("TCP khác UDP ở điểm nào?", "UDP luôn nhanh và có biên nhận", "TCP hướng kết nối và kiểm soát lỗi", "TCP không có cổng", "UDP thay thế địa chỉ IP", "B"),
        ("DNS làm nhiệm vụ gì?", "Đổi tên miền thành địa chỉ IP", "Mã hóa ổ đĩa", "Chấm điểm bài thi", "Lưu fact", "A"),
        ("Cổng mặc định của HTTP là số nào?", "21", "443", "80", "3306", "C"),
        ("Switch thông thường chuyển khung ở tầng nào?", "Tầng ứng dụng", "Tầng mạng", "Tầng vận chuyển", "Tầng liên kết dữ liệu", "D"),
        ("Địa chỉ IP dùng để làm gì?", "Đặt tên hiển thị trên giao diện", "Định danh host trên mạng", "Lưu điểm chuyên cần", "Thay khóa surrogate", "B"),
    ],
    "XSTK": [
        ("Trung bình cộng được tính thế nào?", "Tổng các giá trị chia số quan sát", "Giá trị xuất hiện nhiều nhất", "Hiệu lớn nhất và nhỏ nhất", "Tích các xác suất", "A"),
        ("Một xác suất hợp lệ nằm trong khoảng nào?", "Mọi số nguyên", "Chỉ 0 hoặc 100", "Từ 0 đến 1", "Luôn lớn hơn 1", "C"),
        ("Phương sai mô tả điều gì?", "Số dòng fact", "Độ phân tán quanh trung bình", "Tên chiều", "Thứ tự sắp xếp", "B"),
        ("Hai biến cố độc lập thỏa điều kiện nào?", "P(A) = P(B)", "A và B không cùng không gian", "P(A hoặc B) = 0", "P(A và B) = P(A)P(B)", "D"),
        ("Trung vị là gì?", "Giá trị đứng giữa sau khi sắp xếp", "Luôn bằng trung bình", "Giá trị lớn nhất", "Số lượng phần tử", "A"),
    ],
    "AVCN": [
        ("Từ warehouse trong bài đọc này gần nghĩa nào nhất?", "Câu hỏi", "Kho", "Điểm số", "Mạng", "B"),
        ("Query nghĩa là gì?", "Truy vấn", "Sao lưu", "Chiều", "Học kỳ", "A"),
        ("Primary key dịch sát là gì?", "Khóa ngoại", "Bảng tạm", "Khóa chính", "Dòng tổng", "C"),
        ("Backup nghĩa là gì?", "Xóa lịch sử", "Nối bảng", "Trung bình", "Sao lưu", "D"),
        ("Average nghĩa là gì?", "Cổng", "Giá trị trung bình", "Phiên bản", "Bài giảng", "B"),
    ],
}

HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Vũ", "Đặng", "Bùi", "Đỗ", "Mai", "Lý", "Đinh"]
DEM = ["Minh", "Thu", "Ngọc", "Quốc", "Thanh", "Hữu", "Anh", "Đức", "Phương", "Gia"]
TEN = ["An", "Chi", "Dũng", "Hà", "Khang", "Linh", "My", "Phúc", "Quân", "Trang", "Vy", "Sơn"]


def subject_name(ma_mon: str) -> str:
    for ma, ten, _tin, _khoa in SUBJECTS:
        if ma == ma_mon:
            return ten
    return ma_mon


def exams_for_subject(ma_mon: str):
    ten = subject_name(ma_mon)
    return [
        (f"{ma_mon}_L1", ma_mon, f"Luyện đề {ten}", "LUYEN_DE", "DE", 5, 20),
        (f"{ma_mon}_T1", ma_mon, f"Kiểm tra {ten}", "THI", "TRUNG_BINH", 5, 25),
    ]


def role_of(ma_hs: str) -> str:
    for person in PEOPLE:
        if person[0] == ma_hs:
            return person[6]
    return ""
