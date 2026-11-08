"""Điền bản thảo BTL vào khung mẫu PTIT. Không tạo file Word trắng."""

import re
import shutil
import sys
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph

SKILL_SCRIPTS = Path(r"C:\Users\ADMIN\.agents\skills\ptit-academic-writing\scripts")
sys.path.insert(0, str(SKILL_SCRIPTS))
from docx_tools import backup_docx  # noqa: E402

TEMPLATE = Path(r"E:\Hoc-Tap\Kho Dữ Liệu\Tài liệu học tập\Mẫu Tiểu luận_DW.docx")
DEST = Path(r"E:\Hoc-Tap\Kho Dữ Liệu\BTL_KhoDL\Bao_cao_BTL_Kho_du_lieu_Nhom9.docx")

COVER = {
    "[KHOA CHUYÊN NGÀNH]": "KHOA CÔNG NGHỆ THÔNG TIN 1",
    "[BÁO CÁO BÀI TẬP LỚN / TIỂU LUẬN / ĐỒ ÁN / KHÓA LUẬN]": "BÁO CÁO BÀI TẬP LỚN",
    "[TÊN HỌC PHẦN]": "KHO DỮ LIỆU",
    "[TÊN ĐỀ TÀI BÁO CÁO HOẶC ĐỒ ÁN NGHIÊN CỨU]": "HỆ THỐNG QUẢN LÝ HỌC TẬP VÀ ÔN LUYỆN TRỰC TUYẾN",
    "[HỌ VÀ TÊN GIẢNG VIÊN]": "ThS. Nguyễn Thị Thu Hiên",
    "[HỌ VÀ TÊN SINH VIÊN]": "Nguyễn Quý Tường Anh, Tạ Hoà Bình, Nguyễn Tiến Đạt, Mai Quốc Hưng",
    "[MÃ SINH VIÊN]": "B23DCKD004, B23DCKD008, B23DCKD014, B23DCKD030",
    "[LỚP SINH VIÊN]": "D23CQKD02-B",
    "[NHÓM MÔN HỌC]": "Nhóm 9 (lớp học phần Nhóm 2)",
    "[NĂM]": "2026",
}

BODY = {
    "1. Tính cấp thiết của đề tài": [
        "Học phần Kho dữ liệu yêu cầu nhóm không dừng ở bài tập truy vấn rời mà phải có một sản phẩm chạy được. Đề tài nhóm chọn là hệ thống học tập và ôn luyện trực tuyến: học sinh xem bài, làm đề, nộp bài; cán bộ học vụ đổi lớp, cho bảo lưu hoặc gắn cảnh báo. Những việc này phát sinh liên tục, không phải một file Excel nộp một lần.",
        "Nếu chỉ để bảng tác nghiệp rồi viết báo cáo trực tiếp trên đó, câu hỏi phân tích dễ bị lẫn với giao dịch đang mở. Giảng viên hướng dẫn yêu cầu nhóm 9 có nguồn OLTP mô phỏng, hai fact độc lập, chiều học sinh kiểu SCD Type 2, tầng tổng hợp bằng indexed view và khối đa chiều SSAS. Bản thảo mô tả hệ thống trong thư mục BTL_KhoDL: cổng web nhận nghiệp vụ, ETL đưa dữ liệu vào kho SQL Server, khối SSAS và dashboard đọc trên kho đó.",
    ],
    "2. Mục tiêu nghiên cứu": [
        "Mục tiêu của bài là dựng được kho hình chòm sao cho bài toán học và thi, rồi thao tác được trên giao diện khi bảo vệ trực tiếp. Nhóm không làm slide. Người nghe nhìn sản phẩm đang chạy.",
        "Các đầu việc cụ thể là: nguồn OLTP có học sinh, môn, đề, câu hỏi, bài học, lần nộp và phiên học; fact kết quả thi và fact chuyên cần dùng chung thời gian, học sinh, môn; SCD Type 2 với start_date, end_date, is_current; cổng chất lượng và đối soát số dòng; bảng tổng hợp làm mới sau mỗi mẻ; năm thao tác Roll-up, Drill-down, Slice, Dice, Pivot cùng drill-across; bộ sinh dữ liệu và dashboard.",
    ],
    "3. Đối tượng và phạm vi nghiên cứu": [
        "Đối tượng dữ liệu là học sinh đại học đang học, luyện đề và xem bài trên một hệ mô phỏng. Nhóm sinh 48 học sinh ở bốn lớp D23CQCN01, D23CQKT02, D23CQKD03 và D23CQVT04. Bốn thành viên nhóm có mặt trong danh mục học sinh, mã B23DCKD004, B23DCKD008, B23DCKD014 và B23DCKD030, để thao tác trên dữ liệu mẫu. Báo cáo này là sản phẩm bảo vệ chung của Nhóm 9.",
        "Phạm vi thời gian của dữ liệu lịch sử là các ngày làm việc từ 08/09/2026 đến 03/11/2026, học kỳ HK1 năm học 2026-2027. Sáu môn là Cơ sở dữ liệu, Kho dữ liệu, Lập trình Python, Mạng máy tính, Xác suất thống kê và Tiếng Anh chuyên ngành. Mỗi môn có một đề luyện, một đề kiểm tra (năm câu) và ba bài học. Nguồn không nối vào cổng đào tạo thật của học viện. Kho phòng lab là database DW_QuanLyHocTap trên SQL Server. Khối đa chiều được dựng trong Visual Studio SSDT theo ssas/HUONG_DAN_SSAS_VA_EXCEL.md và được đọc bằng Excel PivotTable.",
    ],
    "4. Phương pháp tiếp cận và công cụ thực thi": [
        "Nhóm thực hiện theo lộ trình giảng viên hướng dẫn: tách OLTP khỏi kho theo hướng Inmon, rồi thiết kế chiều theo bốn bước của Kimball. Cổng web dùng Python 3.12 và FastAPI. Hệ quản trị duy nhất là Microsoft SQL Server. OLTP_QuanLyHocTap giữ tám bảng tác nghiệp đã chuẩn hóa. DW_QuanLyHocTap là kho. Ứng dụng nối bằng pyodbc. Script mockup_generator/generate_sample_data.py nạp kỳ mẫu vào OLTP, ETL sau đó ghi sang kho.",
        "ETL là một vòng lặp nền, khoảng 1,2 giây một lần, đọc bản ghi mới theo watermark. Khi biến môi trường MSSQL_CONN_STR được đặt, mỗi mẻ có dữ liệu mới được đẩy sang SQL Server. Giao diện web một trang gồm sáu màn: bảng điều khiển, cổng học tập, học vụ, dòng dữ liệu, OLAP và chất lượng. Kiểm tra logic nằm ở lệnh python -m app.selfcheck, không phụ thuộc trình duyệt.",
    ],
    "5. Bố cục của báo cáo": [
        "Chương 1 chốt bài toán và các khái niệm được dùng: hạt fact, chiều dùng chung, SCD Type 2, cổng chất lượng, OLAP và drill-across. Chương 2 là thiết kế: kiến trúc web tới SQL Server và SSAS, ma trận bus, hai fact, luật loại bản ghi, unknown member. Chương 3 là cách cài ETL, streaming, đồng bộ SQL Server và giao diện. Chương 4 ghi số đo trên dữ liệu vừa sinh, gồm đối soát dòng, kịch bản kiểm thử biến động học vụ SCD Type 2, kịch bản nộp bài thi hợp lệ, kịch bản bản ghi lỗi và kịch bản đối soát drill-across. Kết luận nêu phần đã chạy và hướng làm mới khối sau mỗi mẻ.",
    ],
    "1.1 Khảo sát bài toán và bối cảnh thực tiễn": [
        "Một buổi học trên hệ thống này có hai việc khác nhau. Việc thứ nhất là nộp bài: hệ thống chấm số câu đúng, quy điểm trên thang 10 và lưu thời gian làm. Việc thứ hai là học bài: học sinh mở video hoặc tài liệu, hệ thống cộng phút, số lần bấm và một điểm chuyên cần nội bộ. Hai việc không cùng mức chi tiết. Một học sinh có thể nộp hai bài Cơ sở dữ liệu nhưng xem bảy phiên bài giảng, hoặc chỉ học mà chưa thi.",
        "Cán bộ học vụ còn sửa hồ sơ: chuyển lớp, bảo lưu, cảnh báo học vụ, rồi cho học tiếp. Nếu bảng học sinh chỉ giữ trạng thái mới nhất, bài thi tháng 9 sẽ bị gắn nhầm vào lớp tháng 10. Câu hỏi cần trả lời khi chấm là liệu fact cũ có bị viết lại hay không. Vì vậy chiều học sinh phải giữ lịch sử, còn fact chỉ trỏ tới phiên bản đúng tại thời điểm nộp.",
        "Bài mẫu chuyển phát nhanh của nhóm 6 đi theo ba tầng: staging, lược đồ sao, rồi khối đa chiều. Nhóm 9 giữ unknown member khóa -1, cổng kiểm tra trước fact và đối soát số dòng. Nguồn web được đọc theo watermark, biến đổi rồi nạp vào kho SQL Server. Khối SSAS lấy data source từ database DW_QuanLyHocTap, không đọc bảng OLTP. Kịch bản bảo vệ vẫn là thêm một dòng ở nguồn, ETL chạy, kho và màn hình đổi số, sau đó process khối để Excel thấy dòng mới.",
    ],
    "1.2 Cơ sở lý thuyết nền tảng": [
        "Inmon mô tả kho là dữ liệu tích hợp, gắn thời gian, ổn định và hướng chủ đề. Ông cũng tách hạt nguyên tử khỏi tầng tổng hợp: hạt nguyên tử giữ sự kiện gốc, tầng trên chỉ để hỏi cho nhanh [1]. Nhóm hiểu ổn định theo nghĩa không sửa điểm một bài đã nạp chỉ vì hôm sau học sinh đổi lớp. Bài đó vẫn là sự kiện của ngày nó xảy ra.",
        "Kimball thiết kế kho từ quy trình nghiệp vụ và mức hạt, rồi mới chọn chiều và số đo. Các fact khác nhau được phép dùng chung một số chiều. Đó là kiến trúc bus. Khi có từ hai fact trở lên mà vẫn dùng chung chiều, lược đồ gọi là fact constellation [2]. Nhóm có đúng hai fact. Chiều dùng chung là thời gian, học sinh và môn. Đề thi chỉ gắn fact kết quả. Bài học chỉ gắn fact chuyên cần.",
        "Cùng tài liệu đó chỉ ra SCD Type 2: khi thuộc tính cần lưu lịch sử thay đổi, đóng bản ghi cũ bằng ngày kết thúc và thêm một bản mới với khóa surrogate khác [2]. Nhóm áp dụng cho lớp và trạng thái học vụ. Họ tên coi như không đổi trong phạm vi bài. Kimball cũng khuyên không nối hai fact trực tiếp khi hạt lệch nhau, vì một bài thi sẽ lặp theo số phiên học và tổng điểm bị nhân lên. Cách làm trên lớp là gộp từng fact về cùng một hạt, rồi FULL OUTER JOIN.",
        "Thuật ngữ OLAP gắn với bài của Codd, Codd và Salley năm 1993: phân tích xoay quanh nhiều chiều chứ không chỉ một câu hỏi tác nghiệp [3]. Năm thao tác nhóm làm trên giao diện là Roll-up (cuộn lên mức thô hơn), Drill-down (khoan xuống mức mịn hơn), Slice (cố định một chiều), Dice (cắt nhiều điều kiện cùng lúc) và Pivot (đổi hàng với cột). Drill-across là thao tác thêm, nối hai fact sau khi đã cùng hạt.",
        "Bước ETL cần một cổng chất lượng trước fact. Kimball và Caserta mô tả việc đo số bản ghi đọc được, số bản ghi nạp và số bản ghi loại, để người vận hành biết dòng có bị rơi giữa đường hay không [4]. Unknown member là lối thoát khi mã học sinh hoặc mã đề không tra được chiều: fact vẫn vào kho với khóa -1, thay vì bị xóa im lặng. Nhóm tách hai việc này. Sai logic của số đo thì loại. Sai mã danh mục thì giữ, nhưng đánh dấu không xác định.",
    ],
    "2.1 Phân tích yêu cầu và kiến trúc hệ thống": [
        "Yêu cầu chức năng bám góp ý của giảng viên hướng dẫn. Nguồn phải nhận bài nộp và phiên học từ form, không chỉ phát file CSV. Quản trị phải đổi được lớp và trạng thái để SCD sinh bản mới ngay trước mắt. Bộ sinh phải bắn nhiều học sinh trong một nhịp, có cả bản ghi bẩn. Dashboard đọc số từ kho, không đọc thẳng bảng OLTP để vẽ điểm trung bình. Trang OLAP trên web và PivotTable trên khối SSAS phải làm được Roll-up, Drill-down, Slice, Dice và Pivot.",
        "Kiến trúc vận hành gồm cổng web, OLTP_QuanLyHocTap, ETL, kho DW_QuanLyHocTap và ba lối đọc. Cổng học sinh ghi bài nộp và phiên học thẳng vào OLTP. ETL kiểm tra số đo, tra chiều, áp dụng SCD Type 2 rồi nạp fact. Kho là fact constellation. Dashboard đọc indexed view, không đọc bảng tác nghiệp để vẽ điểm trung bình. Hình 2.1 mô tả lối đi này.",
        "Nhóm không dựng thêm cơ sở staging vật lý. Watermark trên ba luồng lan_lam_bai, phien_hoc và su_kien_hoc_vu đóng vai trò mốc trích xuất. Bản ghi đã qua mẻ, kể cả bản bị loại, không bị đọc lại. Đây là một hạn chế: nếu sửa đúng dòng bẩn tại chỗ mà giữ nguyên id, kho sẽ không hút lại. Muốn nạp lại thì phải phát sinh id mới. Nhóm chấp nhận điểm này vì bài demo cần vòng lặp ổn định, không kẹt mãi ở một dòng lỗi.",
    ],
    "2.2 Thiết kế chi tiết và cấu trúc dữ liệu": [
        "Nguồn tác nghiệp OLTP_QuanLyHocTap có tám bảng và dừng ở dạng chuẩn 3NF: học sinh, môn học, đề thi, câu hỏi, bài học, lần làm bài, phiên học và sự kiện học vụ. Mỗi thuộc tính phụ thuộc vào khóa của đúng bảng đó, không phụ thuộc bắc cầu. Mã học sinh cố ý không là khóa ngoại của lần nộp, vì nguồn được phép phát sinh mã lạ; kho mới quyết định đưa fact về unknown member. Phần sau của chương dùng tám bảng này làm nguồn cho lược đồ chòm sao.",
        "Mức hạt fact kết quả là một lần nộp đã chấm, khóa tự nhiên là id bảng lan_lam_bai. Số đo gồm điểm, số câu đúng, số câu sai, tổng số câu, tỷ lệ đúng và thời gian làm tính bằng giây. Điểm và tỷ lệ là số đo không cộng được khi cuộn lên; báo cáo cuộn dùng trung bình điểm và tính lại tỷ lệ từ tổng câu đúng chia tổng câu. Mức hạt fact chuyên cần là một phiên học hoàn thành. Số đo là phút học, số video (0 hoặc 1), số tương tác và điểm chuyên cần. Hai hạt này cố ý không bằng nhau. Hình 2.2 đặt hai fact ở giữa, ba chiều dùng chung phía trên và hai chiều riêng phía dưới.",
        "Chiều thời gian sinh sẵn từ 01/08/2026 đến 30/06/2027, khóa là số YYYYMMDD. Thuộc tính có thứ, tuần, tháng, quý, năm, học kỳ và năm học. Tháng 9 đến tháng 12 và tháng 1 thuộc HK1; tháng 2 đến tháng 6 thuộc HK2; tháng 7 là học hè. Chiều môn, đề và bài học là SCD Type 1: đổi tên thì cập nhật tại chỗ. Chiều học sinh là Type 2. Unknown member của mọi chiều dùng khóa -1, mã UNKNOWN, để khóa ngoại của fact không gãy.",
        "Một dòng học sinh trong kho có hoc_sinh_key, mã, họ tên, lớp, trạng thái, lý do, start_date, end_date, is_current và version_no. View vw_dim_hoc_sinh_scd đổi tên cột thành Start_Date, End_Date và Is_Current để đúng chữ trong góp ý. Bản hiện tại có end_date bằng 9999-12-31 23:59:59. Khi có sự kiện mới, ETL đóng bản cũ tại đúng thời điểm sự kiện rồi chèn bản mới. Fact không lấy bản is_current. Fact dò bản có start_date nhỏ hơn hoặc bằng thời điểm phát sinh và end_date lớn hơn thời điểm đó.",
        "Trong một mẻ, sự kiện học vụ được áp dụng hết trước, fact nạp sau. Nhờ vậy bài nộp cùng một nhịp với lần chuyển lớp vẫn tra được phiên bản mới. Bài cũ không bị cập nhật khóa. Kịch bản kiểm thử biến động học vụ SCD Type 2 dùng học sinh mã B23DCKD004: từ 05/09/2026 ở lớp D23CQKD03, từ 12/10/2026 08:00 chuyển sang D23CQCN01. Học sinh HS-BL01 chuyển sang bảo lưu cùng mốc. Học sinh HS-CB01 bị gắn cảnh báo học vụ. Học sinh HS-CC01 chỉ có phiên học, HS-THI01 chỉ có bài thi, để drill-across còn dòng trống một bên.",
        "Cổng chất lượng của bài thi loại các trường hợp: tổng câu không dương, số câu âm, đúng cộng sai khác tổng, điểm ngoài đoạn 0 đến 10, điểm lệch quá 0,05 so với 10 nhân số câu đúng chia tổng câu, tỷ lệ lệch quá 0,02, thời gian không dương hoặc quá bốn giờ. Phiên học bị loại nếu thời lượng không dương hoặc quá tám giờ, số video khác 0 và 1, tương tác âm hoặc quá 200, điểm chuyên cần ngoài 0 đến 10. Mã học sinh không có trong chiều thì không bị loại. Fact nhận hoc_sinh_key = -1.",
        "Tầng tổng hợp trên SQL Server là hai indexed view. iv_diem_theo_mon_thang gom fact thi theo năm, tháng, môn, lớp tại thời điểm thi và loại bài. iv_chuyen_can_theo_lop_tuan gom theo tuần. Cả hai dùng WITH SCHEMABINDING, COUNT_BIG và unique clustered index. Trung bình điểm lấy từ SUM chia số lượt vì indexed view không chứa AVG. Drill-across nằm ở vw_drill_across bằng WITH và FULL OUTER JOIN. View này không được đánh chỉ mục cụm, vì SQL Server không cho outer join trong indexed view. Trên LocalDB, dashboard đọc iv_diem_theo_mon_thang WITH (NOEXPAND) để lấy đúng bản đã tổng hợp.",
        "Khóa ngoại của hai fact có nonclustered index: học sinh, ngày, môn, đề hoặc bài học. Cột loai_bai chỉ có THI và LUYEN_DE, loai_noi_dung chỉ có VIDEO và TAI_LIEU. Giáo trình gán bitmap index cho cột ít giá trị như vậy trên Oracle [5]. SQL Server của bài dùng ix_fact_exam_loai và ix_fact_cc_loai. Không gọi các index này là bitmap.",
    ],
    "3.1 Cài đặt và triển khai chức năng": [
        "Mã nguồn chia theo việc. sql/app_oltp.sql và sql/app_dw.sql là lược đồ ứng dụng tạo trên SQL Server nếu chưa có. sql/06_sqlserver_dw_and_indexed_views.sql là bản dựng lại hai database trong SSMS. mockup_generator/generate_sample_data.py sinh kỳ mẫu với bộ sinh số cố định seed 9, nên mỗi lần chạy lại đều ra 344 bài và 822 phiên. app/etl.py là cổng chất lượng và mẻ ETL. app/olap.py đọc indexed view và fact. app/main.py là API. Hướng dẫn SSDT và Excel nằm ở ssas/HUONG_DAN_SSAS_VA_EXCEL.md.",
        "FastAPI nhận bài nộp, chấm theo đáp án trong OLTP rồi mới ghi lần làm [6]. Form làm đề không gửi đáp án xuống trình duyệt trước khi nộp. Phiên học do server tính điểm: 70 phần trăm theo tỷ lệ thời lượng so với bài chuẩn, 30 phần trăm theo số tương tác nhưng không quá 10 lần bấm, trần là 10 điểm. Video chỉ được tính là đã xem khi bài đó là VIDEO và học sinh xem từ 60 phần trăm thời lượng chuẩn trở lên.",
        "Indexed view được khai báo bằng WITH SCHEMABINDING và unique clustered index [7]. Khối trong SSDT có hai measure group trên hai fact, các hierarchy đã thiết kế, và Excel PivotTable nối vào khối [8].",
        "Bộ sinh mỗi nhịp chọn vài học sinh không thuộc bốn mã B23, trừ khi bật ô đụng thành viên nhóm. Khoảng 40 phần trăm nhịp là nộp bài, còn lại là phiên học. Nếu bật dữ liệu bẩn, khoảng 10 phần trăm bài có điểm 15 và số câu lệch, khoảng 6 phần trăm dùng mã NGOAI_DS nhưng số đo vẫn đúng, và một ít phiên có thời lượng âm. Ba kiểu này cho thấy cùng lúc hàng bị loại và hàng unknown member.",
        "Giao diện nghe WebSocket tại /ws/live. Mỗi lần OLTP phát sinh hoặc một mẻ ETL có việc, dòng nhật ký trên màn hình dòng dữ liệu thêm một dòng. Bảng điều khiển đọc /api/dashboard: điểm trung bình theo môn lấy từ iv_diem_theo_mon_thang, không quét fact. Hình 3.1 chụp bảng điều khiển sau mẻ khởi tạo. Hình 3.2 chụp cổng làm đề của kịch bản nộp bài thi hợp lệ. Trang học vụ vẽ đủ Start_Date, End_Date, Is_Current và liệt kê bài gần đây kèm khóa surrogate.",
    ],
    "3.2 Kết quả thực nghiệm và đánh giá": [
        "Mẻ nạp kỳ mẫu trên SQL Server chạy trong 712 ms. Nguồn có 344 lần nộp và 822 phiên. Kho nhận đủ 344 và 822, loại 0, unknown member bằng 0. Sự kiện học vụ là 51: 48 lần nhập học và 3 lần đổi sau ngày 12/10. Số phiên bản chiều học sinh lớn hơn 0 cũng là 51, trong đó 48 bản đang hiệu lực. Indexed view iv_diem_theo_mon_thang còn 109 dòng, tổng so_luot bằng 344. Ba cờ đối soát khop_bai, khop_phien và khop_summary đều đúng.",
        "Điểm trung bình toàn kho là 6,72. Tổng phút học là 13 197, điểm chuyên cần trung bình 6,71. Theo môn, xác suất thống kê cao nhất với 7,11 điểm trên 56 lượt; kho dữ liệu thấp nhất với 6,38 trên 52 lượt. Tổng lượt sáu môn là 56 + 54 + 60 + 56 + 66 + 52 = 344, khớp fact. Đây là dữ liệu giả lập có kiểm soát, không phải phổ điểm thật của lớp.",
        "Kịch bản kiểm thử biến động học vụ SCD Type 2 cho ra hai phiên bản của học sinh mã B23DCKD004. Bản 1, khóa 1, lớp D23CQKD03, từ 05/09/2026 00:00 đến 12/10/2026 08:00, is_current = 0. Bản 2, khóa 49, lớp D23CQCN01, từ 12/10/2026 08:00, is_current = 1. Bài ngày 28/09 môn xác suất thống kê trỏ khóa 1 và lớp KD03. Bài ngày 20/10 môn cơ sở dữ liệu trỏ khóa 49 và lớp CN01. Hình 3.3 chụp màn hình tra cứu lịch sử này. Self-check đếm thêm: không có bài trước 12/10 gắn bản 2, và không có bài từ 12/10 gắn bản 1. Fact cũ không bị viết lại khi sinh bản mới.",
        "Drill-across trên dữ liệu sạch cho 278 cặp mã học sinh với môn: 186 cặp có cả điểm lẫn phút, 15 cặp chỉ có điểm, 77 cặp chỉ có chuyên cần. FULL OUTER JOIN giữ 92 cặp mà inner join sẽ làm mất. Kịch bản đối soát dùng một học sinh với môn Cơ sở dữ liệu: 5 bài, tổng điểm 26; 7 phiên, tổng 110,5 phút. Nối thẳng hai fact ra 35 dòng, tổng điểm thành 182 và tổng phút thành 552,8. 35 bằng 5 nhân 7, 182 bằng 26 nhân 7. Đó là lý do không JOIN hai bảng fact.",
        "Roll-up từ tháng lên học kỳ gom 3 dòng tháng thành 1 dòng HK1 2026-2027, vẫn 344 lượt, điểm trung bình 6,72, 1 155 câu đúng trên 1 720 câu, tỷ lệ 67,15 phần trăm. Slice môn Kho dữ liệu còn số theo tháng. Dice lớp D23CQKD03, môn Cơ sở dữ liệu, từ 01/09 đến 04/11 còn các tuần có bài. Pivot hàng là lớp, cột là sáu môn. Câu lọc fact_ket_qua_thi theo hoc_sinh_key đi qua nonclustered index ix_fact_exam_hs.",
        "Đo 40 vòng trên cùng máy: đọc iv_diem_theo_mon_thang WITH (NOEXPAND) mất 14,2 ms, quét fact rồi nhóm theo môn và lớp mất 47,2 ms. Fact chỉ có 344 dòng nên chưa phải mức kho thật. Nhóm không viết là indexed view nhanh hơn hàng chục lần. Lợi ích nhìn thấy ngay là số dòng phải đọc giảm từ 344 xuống 109. Indexed view tự bảo trì khi fact thay đổi, dashboard không phải xóa rồi chèn lại một bảng tổng hợp.",
    ],
    "1. Các kết quả định lượng đạt được": [
        "Bài chạy local được bằng run.bat hoặc uvicorn. Sau khi sinh dữ liệu, kho có hai fact, 51 phiên bản học sinh, đối soát dòng nguồn bằng dòng nạp cộng dòng loại, và dashboard đọc tầng tổng hợp. Kịch bản kiểm thử biến động học vụ thể hiện đúng lớp theo từng mốc. Kịch bản nộp bài thi hợp lệ đi từ form vào fact. Kịch bản bản ghi lỗi dừng ở etl_reject. Drill-across cho thấy cả phía bị mất nếu dùng inner join và phía bị nhân nếu nối fact với fact. Năm nút OLAP trả về câu SQL và bảng kết quả.",
        "Self-check tự động phủ các ca cần đối chiếu khi bảo vệ: hạt hai fact, đóng và mở SCD, fact bám phiên bản theo thời gian, bản ghi điểm 15 không vào fact, mã lạ vào khóa -1, fact cũ không đổi khóa khi có bản mới, summary khớp số lượt, roll-up ít dòng hơn drill-down, dice và slice có số, pivot là ma trận chữ nhật.",
    ],
    "2. Hạn chế của đề tài": [
        "Dữ liệu là mô phỏng, câu hỏi trắc nghiệm ngắn, chưa phải đề thi thật. Watermark không xử lý lại dòng đã loại nếu người dùng sửa cùng id. Chưa có đăng nhập, người bảo vệ chọn học sinh trên danh sách. Cột phân loại ít giá trị trên SQL Server dùng nonclustered index, không dùng bitmap của Oracle.",
        "Với 344 dòng fact, chênh lệch thời gian giữa indexed view và quét fact còn nhỏ nếu xét kho hàng triệu dòng. Máy dùng để đo là laptop Windows, Python 3.12. Bộ sinh cố ý tạo dữ liệu bẩn nên không được bật nhầm lúc đang giữ số liệu sạch cho một câu hỏi cụ thể. Bốn thành viên mặc định được loại khỏi bộ sinh để hồ sơ lúc đang trình bày không bị dòng ngẫu nhiên đè lên.",
    ],
    "3. Hướng phát triển mở rộng": [
        "Hướng tiếp theo trên lab là bật proactive caching cho partition MOLAP, khoảng im lặng 10 giây, để Excel Refresh thấy bài nộp mới sau khi ETL đã đẩy sang SQL Server. Hàng bị loại nên tách thành hàng đợi sửa và được nạp lại sau khi OLTP đã chỉnh. Lược đồ hai fact và chiều dùng chung đã cố định nên không phải thiết kế lại khối.",
    ],
}


def set_run_font(run, size=13, bold=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        fonts.set(qn(attr), "Times New Roman")


def format_paragraph(paragraph, *, indent=True, center=False, bold=False, size=13):
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(6)
    fmt.space_after = Pt(6)
    fmt.line_spacing = 1.3
    fmt.first_line_indent = Cm(1 if indent and not bold else 0)
    fmt.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.JUSTIFY
    if paragraph.runs:
        paragraph.runs[0].text = paragraph.runs[0].text
        set_run_font(paragraph.runs[0], size=size, bold=bold)
        for extra in paragraph.runs[1:]:
            set_run_font(extra, size=size, bold=bold)


def insert_after(paragraph, text, *, bold=False, indent=True, center=False, size=13):
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    new_para = Paragraph(new_p, paragraph._parent)
    run = new_para.add_run(text)
    set_run_font(run, size=size, bold=bold)
    format_paragraph(new_para, indent=indent, center=center, bold=bold, size=size)
    return new_para


def delete_paragraph(paragraph):
    element = paragraph._element
    parent = element.getparent()
    if parent is not None:
        parent.remove(element)


def replace_tokens(doc):
    def handle(paragraph):
        for run in paragraph.runs:
            for old, new in COVER.items():
                if old in run.text:
                    run.text = run.text.replace(old, new)

    for paragraph in doc.paragraphs:
        handle(paragraph)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    handle(paragraph)
    for section in doc.sections:
        for paragraph in section.header.paragraphs:
            handle(paragraph)
        for paragraph in section.footer.paragraphs:
            handle(paragraph)


def style_headings(doc):
    for name, size in (("Heading 1", 14), ("Heading 2", 13)):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(12)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.line_spacing = 1.3
        style.paragraph_format.first_line_indent = Cm(0)


def paint_cell(cell, text, bold=False):
    paragraph = cell.paragraphs[0]
    for run in paragraph.runs:
        run.text = ""
    run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
    run.text = text
    set_run_font(run, size=12, bold=bold)
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.space_after = Pt(2)


def fill_abbreviations(doc):
    rows = [
        ("OLTP", "Online Transaction Processing", "Xử lý giao dịch tác nghiệp"),
        ("OLAP", "Online Analytical Processing", "Xử lý phân tích trực tuyến"),
        ("ETL", "Extract, Transform, Load", "Trích xuất, biến đổi và nạp"),
        ("SCD", "Slowly Changing Dimension", "Chiều biến đổi chậm"),
        ("DW", "Data Warehouse", "Kho dữ liệu"),
    ]
    table = doc.tables[0]
    for index, values in enumerate(rows, start=1):
        for col, value in enumerate(values):
            paint_cell(table.rows[index].cells[col], value, bold=False)


def add_table_after(paragraph, caption, headers, data):
    caption_p = insert_after(paragraph, caption, bold=True, indent=False, center=True, size=13)
    table = paragraph.part.document.add_table(rows=1 + len(data), cols=len(headers))
    try:
        table.style = "Table Grid"
    except KeyError:
        pass
    caption_p._p.addnext(table._tbl)
    for col, header in enumerate(headers):
        paint_cell(table.rows[0].cells[col], header, bold=True)
    for row_index, row in enumerate(data):
        for col, value in enumerate(row):
            paint_cell(table.rows[row_index + 1].cells[col], str(value), bold=False)
    tail = OxmlElement("w:p")
    table._tbl.addnext(tail)
    return Paragraph(tail, paragraph._parent)


def insert_figure_after(paragraph, image_path, caption):
    pic_p = OxmlElement("w:p")
    paragraph._p.addnext(pic_p)
    pic_para = Paragraph(pic_p, paragraph._parent)
    pic_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pic_para.paragraph_format.first_line_indent = Cm(0)
    pic_para.paragraph_format.space_before = Pt(6)
    pic_para.paragraph_format.space_after = Pt(2)
    run = pic_para.add_run()
    run.add_picture(str(image_path), width=Cm(14.8))
    return insert_after(pic_para, caption, bold=True, indent=False, center=True, size=13)


def chen_phieu(doc):
    cover = next(p for p in doc.paragraphs if p.text.strip().startswith("HÀ NỘI"))
    breaker = insert_after(cover, "", indent=False, center=True)
    breaker.runs[0].add_break(WD_BREAK.PAGE)
    title = insert_after(
        breaker,
        "PHIẾU PHÂN CÔNG NHIỆM VỤ & ĐÁNH GIÁ NHÓM",
        bold=True,
        indent=False,
        center=True,
        size=14,
    )
    title.style = doc.styles["Heading 1"]
    title.paragraph_format.first_line_indent = Cm(0)
    intro = insert_after(
        title,
        "Nhóm 9, lớp D23CQKD02-B, học phần Kho dữ liệu, lớp học phần Nhóm 2. Giảng viên hướng dẫn: ThS. Nguyễn Thị Thu Hiên.",
        indent=False,
    )
    head = insert_after(intro, "1. Thông tin chung", bold=True, indent=False)
    tail = add_table_after(
        head,
        "Bảng 1. Thông tin phân công bốn thành viên Nhóm 9",
        ["STT", "Họ và tên", "MSSV", "Vai trò chính", "Công việc được giao"],
        [
            ["1", "Nguyễn Quý Tường Anh", "B23DCKD004", "Kiến trúc kho, SCD và ETL", "Thiết kế kiến trúc Kho dữ liệu Fact Constellation, cài đặt SCD Type 2, xây dựng luồng ETL và kiểm soát chất lượng dữ liệu."],
            ["2", "Tạ Hoà Bình", "B23DCKD008", "SQL Server và SSAS", "Triển khai Kho dữ liệu trên SQL Server (SSMS), thiết kế khối đa chiều SSAS Data Cube, phân cấp Hierarchy và kết nối báo cáo OLAP."],
            ["3", "Nguyễn Tiến Đạt", "B23DCKD014", "OLTP và giao diện", "Phát triển hệ thống nguồn OLTP, xây dựng bộ sinh dữ liệu Streaming Simulator và giao diện Web Frontend/Dashboard."],
            ["4", "Mai Quốc Hưng", "B23DCKD030", "Tầng tổng hợp và báo cáo", "Thiết kế tầng tổng hợp (Materialized/Indexed Views), truy vấn đối soát Drill-Across, kiểm thử hiệu năng và biên soạn báo cáo."],
        ],
    )
    head = insert_after(tail, "2. Đánh giá đóng góp cá nhân", bold=True, indent=False)
    tail = add_table_after(
        head,
        "Bảng 2. Đánh giá đóng góp cá nhân",
        ["Tiêu chí", "Trọng số", "Tường Anh", "Hoà Bình", "Tiến Đạt", "Quốc Hưng"],
        [
            ["Hoàn thành nhiệm vụ", "50%", "48", "48", "48", "48"],
            ["Hợp tác, hỗ trợ nhóm", "30%", "28", "28", "28", "28"],
            ["Trình bày, báo cáo", "20%", "19", "19", "19", "19"],
            ["Tổng điểm cá nhân", "100%", "95", "95", "95", "95"],
        ],
    )
    tail = insert_after(
        tail,
        "Điểm cá nhân = Điểm nhóm × 80% + Điểm cá nhân (từ bảng trên) × 20%.",
        indent=False,
    )
    tail = insert_after(tail, "3. Nhận xét của nhóm trưởng", bold=True, indent=False)
    tail = insert_after(
        tail,
        "Trong quá trình thực hiện bài tập lớn, các thành viên đã hoàn thành đúng phần việc được phân công: kiến trúc kho và SCD, triển khai SQL Server cùng khối SSAS, nguồn OLTP cùng giao diện, tầng tổng hợp và báo cáo. Mốc đối soát 344 lần nộp, 822 phiên học và 51 phiên bản học sinh được dùng chung cho bản thảo và kịch bản bảo vệ.",
    )
    tail = insert_after(tail, "Nhóm trưởng: Nguyễn Quý Tường Anh", indent=False)
    tail = insert_after(tail, "4. Xác nhận của giảng viên", bold=True, indent=False)
    tail = insert_after(tail, "Giảng viên hướng dẫn: ThS. Nguyễn Thị Thu Hiên", indent=False)
    tail = insert_after(tail, "Điểm bài tập lớn: ............", indent=False)
    tail = insert_after(tail, "Nhận xét: ................................................................", indent=False)
    insert_after(tail, "(Ký tên và ghi điểm cuối cùng)", indent=False, center=True)


HINH_DIR = Path(__file__).resolve().parent / "hinh"
FIGURES = [
    ("Hình 2.1 mô tả lối đi này.", ["hinh_2_1_kien_truc.png"], "Hình 2.1: Sơ đồ kiến trúc tổng thể hệ thống"),
    ("Hình 2.2 đặt hai fact", ["hinh_2_2_chom_sao.png"], "Hình 2.2: Lược đồ hình chòm sao của hai fact và các chiều"),
    ("Hình 3.1 chụp bảng điều khiển", ["hinh_3_1_dashboard.png"], "Hình 3.1: Bảng điều khiển pipeline và số liệu kho"),
    ("Hình 3.2 chụp cổng làm đề", ["hinh_3_2_lam_de.png"], "Hình 3.2: Giao diện làm đề và nộp bài"),
    ("Hình 3.3 chụp màn hình", ["hinh_3_3_scd.png"], "Hình 3.3: Kịch bản kiểm thử biến động học vụ SCD Type 2"),
    ("Hình 4.1 chụp bảng drill-across", ["hinh_4_1_drill_across.png"], "Hình 4.1: Kịch bản đối soát drill-across trên giao diện"),
    ("Hình 4.2 là kết quả câu", ["hinh_4_2_ssms_query.png", "hinh_4_1_ssms_query.png"], "Hình 4.2: Kết quả drill-across trên SQL Server"),
    ("Hình 4.3 là Data Source View", ["hinh_4_3_ssas_dsv.png", "hinh_4_2_ssas_dsv.png"], "Hình 4.3: Data Source View và hierarchy của khối SSAS"),
]


def _anh_co_san(names):
    for name in names:
        path = HINH_DIR / name
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None


def chen_hinh(doc):
    inserted = []
    missing = []
    tail_of = {}
    for needle, names, caption in FIGURES:
        found = [p for p in doc.paragraphs if needle in p.text]
        path = _anh_co_san(names)
        if path is None:
            missing.append(names[0])
            continue
        if not found:
            missing.append(names[0] + " (không thấy chỗ chèn)")
            continue
        anchor = tail_of.get(found[0]._p, found[0])
        cap = insert_figure_after(anchor, path, caption)
        tail_of[found[0]._p] = insert_after(cap, "Nguồn: Nhóm thực hiện", indent=False, center=True, size=11)
        inserted.append(caption)
    if missing:
        print("Chưa có ảnh, bỏ qua:", ", ".join(missing))
    return inserted


def apply_heading_styles(doc, body_start):
    h1_prefixes = (
        "PHẦN MỞ ĐẦU",
        "CHƯƠNG ",
        "KẾT LUẬN",
        "TÀI LIỆU THAM KHẢO",
        "DANH MỤC BẢNG",
    )
    for index, paragraph in enumerate(doc.paragraphs):
        if index < body_start:
            continue
        text = paragraph.text.strip()
        if text.startswith(h1_prefixes):
            paragraph.style = doc.styles["Heading 1"]
            paragraph.paragraph_format.first_line_indent = Cm(0)
        elif re.match(r"^\d+(\.\d+)*\.?\s+\S", text) and not text.startswith("["):
            paragraph.style = doc.styles["Heading 2"]
            paragraph.paragraph_format.first_line_indent = Cm(0)


def _dat_doan(paragraph, text):
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            run.text = ""
        set_run_font(paragraph.runs[0], size=13, bold=paragraph.runs[0].bold)
    else:
        run = paragraph.add_run(text)
        set_run_font(run, size=13, bold=False)


def _chen_truoc(paragraph, text):
    new_p = OxmlElement("w:p")
    paragraph._p.addprevious(new_p)
    para = Paragraph(new_p, paragraph._parent)
    run = para.add_run(text)
    set_run_font(run, size=13, bold=True)
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.first_line_indent = Cm(0)
    return para


def _them_cot(table):
    tbl = table._tbl
    grid = tbl.tblGrid
    cols = grid.findall(qn("w:gridCol"))
    grid.append(deepcopy(cols[-1]))
    for row in tbl.findall(qn("w:tr")):
        cells = row.findall(qn("w:tc"))
        row.append(deepcopy(cells[-1]))


def _cat_tu(doc, start_text):
    body = doc.element.body
    start = None
    for child in list(body):
        if child.tag != qn("w:p"):
            continue
        text = "".join(node.text or "" for node in child.iter(qn("w:t"))).strip()
        if text.startswith(start_text):
            start = child
            break
    if start is None:
        raise SystemExit(f"Không thấy mốc '{start_text}' trong file mẫu")
    removing = False
    for child in list(body):
        if child is start:
            removing = True
        if removing and child.tag != qn("w:sectPr"):
            body.remove(child)


def _tieu_de(anchor, text, level):
    para = insert_after(anchor, text, bold=True, indent=False, size=14 if level == 1 else 13)
    para.style = para.part.document.styles["Heading 1" if level == 1 else "Heading 2"]
    para.paragraph_format.first_line_indent = Cm(0)
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER if level == 1 else WD_ALIGN_PARAGRAPH.LEFT
    return para


def main():
    if not TEMPLATE.exists():
        raise SystemExit(f"Không thấy khung mẫu: {TEMPLATE}")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    if DEST.exists():
        backup_docx(DEST)
    shutil.copy2(TEMPLATE, DEST)
    doc = Document(str(DEST))
    style_headings(doc)

    hoc_vien = next(p for p in doc.paragraphs if p.text.strip().startswith("HỌC VIỆN"))
    if not any(p.text.strip().startswith("BỘ THÔNG TIN") for p in doc.paragraphs):
        _chen_truoc(hoc_vien, "BỘ THÔNG TIN VÀ TRUYỀN THÔNG")
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text.startswith("ĐỀ TÀI"):
            _dat_doan(paragraph, "ĐỀ TÀI: HỆ THỐNG QUẢN LÝ HỌC TẬP VÀ ÔN LUYỆN TRỰC TUYẾN")
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif text.startswith("Hà Nội"):
            _dat_doan(paragraph, "Hà Nội, tháng 11 năm 2026")
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    bia = doc.tables[0]
    paint_cell(bia.rows[0].cells[2], "ThS. Nguyễn Thị Thu Hiên", bold=False)
    paint_cell(bia.rows[1].cells[2], "Hệ thống quản lý học tập và ôn luyện trực tuyến", bold=False)
    paint_cell(bia.rows[2].cells[2], "Nhóm 9, lớp D23CQKD02-B", bold=False)
    thanh_vien = [
        "Nguyễn Quý Tường Anh – B23DCKD004",
        "Tạ Hoà Bình – B23DCKD008",
        "Nguyễn Tiến Đạt – B23DCKD014",
        "Mai Quốc Hưng – B23DCKD030",
    ]
    if len(bia.rows) < 7:
        bia.add_row()
    for index, name in enumerate(thanh_vien):
        paint_cell(bia.rows[3 + index].cells[2], name, bold=False)

    viec = doc.tables[1]
    cong_viec = [
        ["1", "Nguyễn Quý Tường Anh", "B23DCKD004", "Kiến trúc kho, SCD và ETL", "Thiết kế fact constellation, SCD Type 2, luồng ETL và cổng chất lượng."],
        ["2", "Tạ Hoà Bình", "B23DCKD008", "SQL Server và SSAS", "Lược đồ SQL Server, indexed view, khối SSAS và hướng dẫn Excel."],
        ["3", "Nguyễn Tiến Đạt", "B23DCKD014", "OLTP và giao diện", "Tám bảng OLTP 3NF, cổng nộp bài và dashboard."],
        ["4", "Mai Quốc Hưng", "B23DCKD030", "Tổng hợp và báo cáo", "Đối soát drill-across, đo indexed view và biên soạn báo cáo."],
    ]
    while len(viec.rows) < 5:
        viec.add_row()
    for row_index, values in enumerate(cong_viec, start=1):
        for col, value in enumerate(values):
            paint_cell(viec.rows[row_index].cells[col], value, bold=False)

    diem = doc.tables[2]
    if len(diem.columns) < 6:
        _them_cot(diem)
    bang_diem = [
        ["Tiêu chí", "Trọng số", "Tường Anh", "Hoà Bình", "Tiến Đạt", "Quốc Hưng"],
        ["Hoàn thành nhiệm vụ", "50%", "48", "48", "48", "48"],
        ["Hợp tác, hỗ trợ nhóm", "30%", "28", "28", "28", "28"],
        ["Trình bày, báo cáo", "20%", "19", "19", "19", "19"],
        ["Tổng điểm cá nhân", "100%", "95", "95", "95", "95"],
    ]
    for row_index, values in enumerate(bang_diem):
        for col, value in enumerate(values):
            paint_cell(diem.rows[row_index].cells[col], value, bold=row_index == 0)

    for paragraph in doc.paragraphs:
        if paragraph.text.strip().startswith("Trong quá trình thực hiện"):
            _dat_doan(
                paragraph,
                "Trong quá trình thực hiện tiểu luận, các thành viên hoàn thành phần việc đã phân công: kiến trúc kho và SCD, SQL Server cùng khối SSAS, nguồn OLTP cùng giao diện, tầng tổng hợp và báo cáo. Mốc đối soát dùng chung là 344 lần nộp, 822 phiên học và 51 phiên bản học sinh. Nhóm trưởng xác nhận bảng điểm 48, 28 và 19 theo trọng số 50%, 30% và 20%.",
            )

    _cat_tu(doc, "DANH MỤC THUẬT NGỮ")
    anchor = next(p for p in doc.paragraphs if "Ký tên" in p.text)
    anchor = _tieu_de(anchor, "DANH MỤC THUẬT NGỮ VIẾT TẮT", 1)
    anchor = add_table_after(
        anchor,
        "Bảng 0.1. Thuật ngữ dùng trong báo cáo",
        ["Viết tắt", "Tiếng Anh", "Tiếng Việt"],
        [
            ["OLTP", "Online Transaction Processing", "Xử lý giao dịch tác nghiệp"],
            ["OLAP", "Online Analytical Processing", "Xử lý phân tích trực tuyến"],
            ["ETL", "Extract, Transform, Load", "Trích xuất, biến đổi và nạp"],
            ["SCD", "Slowly Changing Dimension", "Chiều biến đổi chậm"],
            ["3NF", "Third Normal Form", "Dạng chuẩn ba"],
            ["SSAS", "SQL Server Analysis Services", "Dịch vụ phân tích của SQL Server"],
        ],
    )
    anchor = _tieu_de(anchor, "DANH MỤC BẢNG", 1)
    for line in [
        "Bảng 2.1. Ma trận bus của hai fact",
        "Bảng 2.2. Mức hạt và số đo",
        "Bảng 4.1. Số đo sau mẻ nạp kỳ mẫu",
        "Bảng 4.2. Đối chứng drill-across và join thẳng hai fact",
    ]:
        anchor = insert_after(anchor, line, indent=False)
    hinh_moc = _tieu_de(anchor, "DANH MỤC HÌNH VẼ", 1)

    truoc_khoa = {
        "1. Tính cấp thiết của đề tài": "LỜI NÓI ĐẦU",
        "1.1 Khảo sát bài toán và bối cảnh thực tiễn": "CHƯƠNG 1. TỔNG QUAN BÀI TOÁN VÀ CƠ SỞ LÝ THUYẾT",
        "2.1 Phân tích yêu cầu và kiến trúc hệ thống": "CHƯƠNG 2. NGUỒN OLTP 3NF VÀ THIẾT KẾ KHO DỮ LIỆU",
        "3.1 Cài đặt và triển khai chức năng": "CHƯƠNG 3. HIỆN THỰC HÓA ETL, INDEXED VIEW VÀ GIAO DIỆN",
    }
    anchor = hinh_moc
    for key, paragraphs in BODY.items():
        if key in truoc_khoa:
            anchor = _tieu_de(anchor, truoc_khoa[key], 1)
        if key == "1. Các kết quả định lượng đạt được":
            for text, level in _CHUONG_4:
                if level:
                    anchor = _tieu_de(anchor, text, level)
                else:
                    anchor = insert_after(anchor, text)
        anchor = _tieu_de(anchor, key, 2)
        for text in paragraphs:
            anchor = insert_after(anchor, text)
    anchor = _tieu_de(anchor, "TÀI LIỆU THAM KHẢO", 1)
    for text in _TAI_LIEU:
        anchor = insert_after(anchor, text, indent=False)

    hinh_da_chen = chen_hinh(doc)
    moc = hinh_moc
    for line in hinh_da_chen:
        moc = insert_after(moc, line, indent=False)

    end_22 = next(p for p in doc.paragraphs if p.text.startswith("Khóa ngoại của hai fact"))
    end_22 = add_table_after(
        end_22,
        "Bảng 2.1. Ma trận bus của hai fact",
        ["Chiều", "Fact kết quả thi", "Fact chuyên cần", "Vai trò"],
        [
            ["Thời gian", "Có", "Có", "Dùng chung"],
            ["Học sinh (SCD Type 2)", "Có", "Có", "Dùng chung"],
            ["Môn học", "Có", "Có", "Dùng chung"],
            ["Đề thi", "Có", "Không", "Riêng fact thi"],
            ["Bài học", "Không", "Có", "Riêng fact chuyên cần"],
        ],
    )
    add_table_after(
        end_22,
        "Bảng 2.2. Mức hạt và số đo",
        ["Fact", "Một dòng là", "Số đo chính", "Cách cuộn lên"],
        [
            ["fact_ket_qua_thi", "Một lần nộp đã chấm", "Điểm, câu đúng, tỷ lệ, giây", "Đếm lượt, trung bình điểm, tỷ lệ tính lại từ tổng câu"],
            ["fact_chuyen_can", "Một phiên học xong", "Phút, video, tương tác, điểm CC", "Cộng phút và video, trung bình điểm CC"],
        ],
    )
    tail = next(p for p in doc.paragraphs if p.text.startswith("Chỉ số 14,2 ms"))
    tail = add_table_after(
        tail,
        "Bảng 4.1. Số đo sau mẻ nạp kỳ mẫu",
        ["Chỉ tiêu", "Giá trị"],
        [
            ["Lần nộp ở OLTP và trong fact", "344"],
            ["Phiên học ở OLTP và trong fact", "822"],
            ["Bản ghi bị loại / unknown member", "0 / 0"],
            ["Phiên bản SCD / bản đang hiệu lực", "51 / 48"],
            ["Dòng iv_diem_theo_mon_thang", "109"],
            ["Điểm thi trung bình", "6,72"],
            ["Tổng phút học / điểm chuyên cần TB", "13 197 / 6,71"],
            ["Thời gian mẻ nạp kỳ mẫu", "712 ms"],
            ["40 vòng đọc indexed view / quét fact", "14,2 ms / 47,2 ms"],
        ],
    )
    add_table_after(
        tail,
        "Bảng 4.2. Kịch bản đối soát drill-across: một học sinh và môn Cơ sở dữ liệu",
        ["Cách tính", "Số dòng", "Tổng điểm", "Tổng phút"],
        [
            ["Gộp từng fact rồi mới nối", "5 bài và 7 phiên", "26", "110,5"],
            ["JOIN thẳng hai fact", "35 = 5 × 7", "182 = 26 × 7", "552,8 ≈ 110,5 × 5"],
        ],
    )
    doc.save(str(DEST))
    print(f"Đã ghi {DEST}")


_CHUONG_4 = [
    ("CHƯƠNG 4. THỰC NGHIỆM OLAP, SCD VÀ ĐỐI SOÁT", 1),
    ("4.1 Kịch bản kiểm tra từ nguồn tới kho", 2),
    ("Nhóm kiểm tra theo đúng thứ tự sẽ nói khi bảo vệ. Trước hết mở bảng điều khiển lúc dữ liệu vừa sinh, chưa bật bộ sinh. Các số phải là 344 bài, 822 phiên, 0 bản ghi loại, 109 dòng indexed view, 51 phiên bản SCD và 48 học sinh hiện tại. Nếu lệch, chạy lại mockup_generator/generate_sample_data.py và đợi mẻ ETL.", 0),
    ("Kịch bản kiểm thử biến động học vụ SCD Type 2 mở trang học vụ với học sinh mã B23DCKD004. Phải thấy hai dòng: End_Date của bản 1 trùng Start_Date của bản 2, chỉ một dòng Is_Current bằng 1. Bảng bài gần đây phải có cả khóa 1 lẫn khóa 49. Tiếp theo chạy kịch bản cảnh báo học vụ. Bản 3 mở ra, các bài tháng 9 và tháng 10 vẫn nằm ở khóa cũ.", 0),
    ("Kịch bản nộp bài thi hợp lệ gửi một bài luyện Cơ sở dữ liệu điểm 8,0. API trả về khóa học sinh và số phiên bản đang gắn với bài đó. Kịch bản kiểm thử bản ghi lỗi tạo điểm 15, số câu lệch và thời gian âm. Hàng này nằm trong etl_reject, không có trong fact_ket_qua_thi. Trang chất lượng phải vẫn đúng đẳng thức nguồn = nạp + loại.", 0),
    ("4.2 Đọc kết quả phân tích và chỗ số liệu dễ bị nhân", 2),
    ("Trên trang OLAP, Roll-up đang để mức học kỳ cho ra một dòng HK1 2026-2027. Drill-down cùng học kỳ đó trả ba tháng 9, 10 và 11. Slice cố định môn Kho dữ liệu. Dice cắt thêm lớp D23CQKD03 và khoảng ngày. Pivot xoay lớp với môn. Mỗi lần bấm, ô SQL phía dưới là câu vừa thực thi.", 0),
    ("Kịch bản đối soát drill-across dùng học sinh B23DCKD004 và môn Cơ sở dữ liệu vì tích 5 nhân 7 đủ nhỏ để nhẩm trên bảng. Câu là WITH rồi FULL OUTER JOIN, không nối hai fact. Hình 4.1 chụp bảng drill-across trên giao diện. Hình 4.2 là kết quả câu drill-across trên SSMS. Hình 4.3 là Data Source View trong SSDT. Một dòng đã gộp giữ tổng điểm 26 và 110,5 phút; nối thẳng hai fact thành 35 dòng.", 0),
    ("Chỉ số 14,2 ms và 47,2 ms là 40 vòng đo liên tiếp trên kho 344 dòng, không phải trung bình của nhiều máy. Số được ghi lại để khỏi phóng đại. Nonclustered index ix_fact_exam_hs phục vụ lọc theo học sinh. Bitmap thuộc về đối chiếu giáo trình Oracle [5]. SQL Server của bài không tạo bitmap index.", 0),
]

_TAI_LIEU = [
    "[1] W. H. Inmon, Building the Data Warehouse, 4th ed. Indianapolis, IN, USA: Wiley, 2005.",
    "[2] R. Kimball and M. Ross, The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling, 3rd ed. Indianapolis, IN, USA: Wiley, 2013.",
    '[3] E. F. Codd, S. B. Codd, and C. T. Salley, "Providing OLAP to user-analysts: An IT mandate," E.F. Codd & Associates, 1993.',
    "[4] R. Kimball and J. Caserta, The Data Warehouse ETL Toolkit. Indianapolis, IN, USA: Wiley, 2004.",
    '[5] Oracle, "Indexes and index-organized tables," Oracle Database Concepts, 19c. [Online]. Available: https://docs.oracle.com/en/database/oracle/oracle-database/19/cncpt/indexes-and-index-organized-tables.html. (Truy cập: 04/11/2026).',
    '[6] S. Ramírez, "FastAPI documentation," 2026. [Online]. Available: https://fastapi.tiangolo.com/. (Truy cập: 04/11/2026).',
    '[7] Microsoft, "Create indexed views," SQL Server documentation. [Online]. Available: https://learn.microsoft.com/en-us/sql/relational-databases/views/create-indexed-views. (Truy cập: 05/11/2026).',
    '[8] Microsoft, "Multidimensional model databases (SSAS)," Analysis Services documentation. [Online]. Available: https://learn.microsoft.com/en-us/analysis-services/multidimensional-models/multidimensional-model-databases-ssas. (Truy cập: 05/11/2026).',
]


if __name__ == "__main__":
    main()
