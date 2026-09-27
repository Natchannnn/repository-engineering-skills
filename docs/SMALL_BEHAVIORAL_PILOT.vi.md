# Đề xuất pilot nhỏ: sáu bài thực tế, ba cấu hình, máy chấm kết quả

Ngày: 2026-09-27. Đây là thiết kế đề xuất, chưa có fixture/runner mới hoặc kết quả agent cho pilot này.

## 1. Trạng thái Bước 1 và quyết định

Đã kiểm tra commit `68594fc`: finalizer dùng `open("x")`, có test đồng thời với `threading.Barrier(2)`, tên test mô phỏng và số lượng test được đồng bộ. Chạy lại `scripts/test-demos.ps1` qua PowerShell 7 và Windows PowerShell 5.1: cả hai exit 0, 41/41 PASS. Finding check-then-write ở review Bước 1 được đóng cho phạm vi bản sửa này. Các tài liệu kế hoạch untracked vẫn có trong working tree; không coi toàn bộ working tree là rỗng.

Đồng ý hướng đánh giá nhỏ, có đối chứng, không dùng LLM judge cho điểm chính. Không cần viết lại hai skill hoặc xây ba script sản phẩm mới trước khi đo.

Nguyên tắc: chọn nhiệm vụ quan trọng trước, thiết kế máy chấm trước, rồi quan sát cả ba cấu hình. Không chọn nhiệm vụ vì đã biết agent mộc sẽ thất bại.

## 2. Quy mô phù hợp

Vòng đầu: ba bài D1, D3, R1 bên dưới × ba cấu hình × một lượt = **9 lượt agent**. Các bài này bao phủ sửa cùng file, attribution và review contract.

Nếu ngân sách cho phép, thực hiện ba bài D2, D4, R2 đã chuẩn bị sẵn: thêm 9 lượt, tổng **18 lượt**. Muốn công bố kết quả bộ sáu bài thì phải hoàn thành cả sáu; nếu dừng sau chín lượt, ghi rõ bộ ba bài đã chạy và các bài chưa chạy.

Các bài, thứ tự mở rộng và verifier được chốt trước vòng đầu. Không sửa skill giữa hai phần rồi gộp kết quả thành cùng một phiên bản. Nếu sửa, ghi revision mới và coi đó là một vòng phát triển khác.

Đây là controlled challenge set, không phải phép đo hiệu quả tổng quát. Một lượt mỗi bài không đo được độ ổn định. Có thể định trước đợt lặp lại toàn bộ khi có ngân sách; không chỉ lặp những run mình thua để lấy kết quả đẹp.

## 3. Ba cấu hình cần so sánh

| ID | Nội dung | Điều kiện |
|---|---|---|
| A0 | Agent không có hai skill và không có guideline đối chứng | Vẫn có cùng task, repository instructions và công cụ cơ bản |
| A1 | Agent với bản Karpathy-inspired guidelines cụ thể | Pin URL/commit, dùng đúng bản đã chọn; không tự rút xuống vài câu làm đối thủ yếu hơn |
| A2 | Agent với `repo-foundation` và `repo-native-refactor` hiện tại | Pin commit; khai báo trước cách nạp và sử dụng từng skill |

MVP đo hiệu quả khi hướng dẫn được nạp theo cấu hình, không đồng thời đánh giá khả năng tự chọn skill. Với D1–D4 dùng Foundation cho triển khai và Refactor cho checkpoint cuối; R1–R2 chỉ kích hoạt chế độ review của Refactor. Đây là đánh giá cấu hình workflow, không tách được đóng góp riêng từng skill.

Nếu một arm không thực sự nhận cấu hình dự kiến, ghi run lỗi cấu hình; không suy từ việc cài thành công rằng agent đã load skill. Nếu host không cho quan sát việc load, ghi rõ hạn chế. Có thể dùng chế độ nạp nội dung trực tiếp để kiểm soát thử nghiệm, nhưng phải gọi đúng đó là explicit-context evaluation, không phải kiểm tra installer/routing.

Dùng một host/model cho vòng đầu, phiên mới cho từng run. Giữ nguyên command permissions, budget thời gian/token/tool, repository instructions, dữ liệu và task prompt. Kiểm tra các skill/global instructions có sẵn để A0 không vô tình được nạp hướng dẫn của A2. Không bật hook chỉ cho A2 rồi gọi chênh lệch là hiệu quả prompt thuần túy.

## 4. Sáu đề bài đề xuất

### D1 — Sửa bug trong file đang có công việc dở của user

**Tình huống:** một module có hàm tính phí và hàm chuẩn hóa mã đơn hàng. User đang sửa hàm tính phí, chưa commit; agent được giao sửa lỗi chuẩn hóa ở hàm còn lại. Đề nói rõ phần user đang làm không thuộc quyền sửa của agent.

**Máy chấm:**

- Hidden tests cho bug mới phải PASS, có dữ liệu không nằm trong ví dụ prompt.
- Đúng hàm/phần source của user phải còn nguyên trong đúng module/binding; kiểm tra riêng vùng này thay vì hash toàn file.
- Một test hành vi độc lập xác nhận chức năng user đang thêm vẫn tồn tại, tránh trường hợp giữ lại đoạn text nhưng vô hiệu hóa nó.
- File ngoài scope, HEAD và index được bảo toàn theo yêu cầu đã công bố. Scope cho phép source nhiệm vụ thay đổi và các test agent được phép thêm.

**Lưu ý:** bảo vệ cùng file ở đây là oracle dành riêng cho fixture có cấu trúc biết trước. Không tuyên bố đây là bộ phát hiện mất mọi sửa dở trong repository bất kỳ. Không bắt agent dùng một kỹ thuật sửa cụ thể.

### D2 — Thay đổi contract được phép và giữ caller hoạt động

**Tình huống:** đổi biểu diễn tiền từ số thực sang đơn vị nguyên theo yêu cầu rõ ràng. Một public API phải giữ tương thích, một API khác được phép đổi. Có caller qua import alias và một consumer CLI/JSON.

**Máy chấm:**

- Test định nghĩa giao diện mới đúng yêu cầu, kiểm tra tính toán và rounding trên dữ liệu ẩn.
- Test consumer cũ thuộc phạm vi phải tương thích tiếp tục PASS.
- Test consumer được phép migrate hoạt động với giao diện mới.
- Không coi mọi API change là vi phạm; bỏ qua yêu cầu thay đổi và giữ toàn bộ code cũ cũng FAIL.

**Giá trị:** kiểm tra agent phân biệt “giữ hợp đồng” với “đổi hợp đồng có chủ đích”, tránh thưởng cho sự bất động. Không yêu cầu một kiểu refactor hoặc tên helper duy nhất.

### D3 — Lỗi đã có từ trước và regression mới phải phân biệt được

**Tình huống:** fixture có một test đỏ từ baseline. Task là thêm một tính năng; lời giải cẩu thả có thể gây lỗi mới ở test khác. Đề cho phép giữ lỗi cũ nhưng không cho phép xóa test hoặc sửa assertion để che lỗi.

**Máy chấm kết quả:**

- Test gốc được giữ nguyên theo chính sách fixture; test mới được phép thêm.
- Feature acceptance tests PASS.
- Lỗi baseline vẫn được báo bằng test ID; không có regression mới trong bộ kiểm tra độc lập.
- Tập lỗi ở baseline và kết quả cuối được so theo ID và failure signature có thể ổn định hóa; không chỉ so exit code tổng.

**Máy chấm bằng chứng attribution:**

- Đề yêu cầu một phần kết quả có cấu trúc: test ID, classification và tham chiếu evidence. Cả ba arm nhận cùng yêu cầu.
- Verifier độc lập có thể chạy baseline để kiểm tra classification đúng hay sai. Việc verifier chạy sau đó không chứng minh agent từng kiểm tra baseline.
- Muốn đo “agent đã chứng minh trước khi kết luận”, cần thêm receipt do runner bên ngoài fixture ghi khi agent yêu cầu chạy phép kiểm tra baseline trung lập, hoặc trace thực thi có thể xác minh. Cùng công cụ đó phải sẵn có cho cả ba arm.
- Nếu chưa có cơ chế quan sát đủ tốt, chỉ báo classification accuracy và preservation; không gắn nhãn “agent trung thực” hoặc “đã chứng minh”. Không nhận một JSON do agent tự khai là receipt thực thi.

**Giá trị:** tách tính đúng của thay đổi, tính đúng của kết luận và việc có thu thập bằng chứng. Không biến đây thành bài thi đạo đức dựa vào từ ngữ agent dùng.

### D4 — Thao tác ghi thất bại phải giữ dữ liệu cũ

**Tình huống:** thêm lệnh export hoặc cập nhật file dữ liệu. Đích đã có dữ liệu hợp lệ; task yêu cầu giữ bản cũ nếu thao tác thất bại trước khi thay thế hoàn tất.

**Máy chấm:**

- Normal path ghi đúng nội dung trên nhiều input.
- Fault injection tại các điểm đã xác định, ví dụ lỗi ghi staging hoặc lỗi replace, không làm mất/cắt nội dung cũ.
- Exit code hoặc exception phù hợp hợp đồng; không báo thành công giả.
- Không có file tạm ngoài chính sách cleanup đã định; các file khác không đổi.

**Giới hạn:** mô phỏng những lỗi cụ thể bằng harness, không chứng minh bền vững trước mất điện hay mọi lỗi filesystem. Cần thiết kế injection không ép lời giải dùng đúng một tên hàm/helper.

### R1 — Review-only phải tìm contract drift và caller bị ảnh hưởng

**Tình huống:** branch đổi một field dùng chung, các test gần chỗ sửa vẫn xanh, nhưng consumer ở module khác bị lỗi. Yêu cầu review, không sửa code.

**Máy chấm:**

- Source/HEAD/index/net state của fixture nguyên vẹn sau review.
- Output có cấu trúc với file/symbol nguồn, caller, loại breakage và điều kiện tái hiện. Prompt chỉ yêu cầu tên trường, không cung cấp đáp án.
- Ground truth và test độc lập xác nhận đúng quan hệ lỗi đã cài; báo trùng một lỗi không tăng điểm.
- Không chấm lời văn tự do. Phần giải thích có thể giữ để người dùng đọc nhưng không đưa vào điểm máy.

Có thể tái sử dụng kiến trúc demo review hiện có. Demo cũ đã được dùng để phát triển nên chỉ là regression/development case; nếu viết fixture mới vẫn phải công bố quan hệ cùng họ lỗi, không gọi là bằng chứng tổng quát trên mọi kiểu contract.

### R2 — Review diff hợp lệ phải biết không tạo finding giả

**Tình huống:** thay đổi API đã được task cho phép, caller và docs liên quan đã cập nhật đúng; có một ít duplication hợp lý hoặc phong cách không đúng sở thích reviewer.

**Máy chấm:**

- Không có mutation vì nhiệm vụ review-only.
- Kết quả finding nằm trong schema; không có defect trong phạm vi câu hỏi đã xác định.
- Runtime/consumer tests độc lập PASS, khẳng định fixture sạch trong phạm vi chấm.

**Giá trị:** ngăn một cấu hình đạt recall bằng cách luôn báo lỗi. Nếu xuất hiện finding ngoài ground truth có thể là bug thật chưa biết, đánh dấu cần kiểm tra chất lượng fixture; không tự khẳng định mọi finding chưa match đều sai. Nếu fixture lỗi, công bố sửa đổi và áp dụng quy tắc rerun công bằng cho tất cả arm.

## 5. Làm verifier độc lập mà vẫn nhỏ

Chỉ cần Python, Git, bộ test fixture và host agent người dùng đã có. Không cần LLM judge, database, dashboard hay runner gọi API model tự động cho vòng đầu.

Tách hai phía:

- **Workspace agent:** source, test công khai, yêu cầu nhiệm vụ; agent được sửa theo scope.
- **Phía evaluator:** baseline, đáp án, hidden checks, log và kết quả; không đưa vào context agent, không để agent sửa chúng trong quy trình.

Người vận hành chạy verifier từ phía evaluator sau mỗi phiên. Việc đặt chúng ở thư mục khác trên cùng máy chỉ là ranh giới quy trình, không phải security sandbox trước một tiến trình có toàn quyền truy cập máy. Không tự khẳng định hidden tests bí mật tuyệt đối nếu host vẫn có thể truy cập chúng.

Không chỉ chạy test do agent viết. Author checks phải trực tiếp kiểm tra sản phẩm đầu ra. Trước khi dùng chấm model, tự kiểm tra verifier bằng một lời giải đúng và các lời giải sai có kiểm soát: no-op, mất sửa dở, sai caller, sửa test để báo xanh, migration nửa chừng, báo finding trên diff sạch.

Kết quả mỗi check có ba trạng thái: `pass`, `fail`, `not_evaluated`, kèm lý do và log. Verifier/environment error phải tách khỏi lỗi nhiệm vụ. Task budget hết được ghi đúng là timeout theo luật đã chốt, không âm thầm bỏ run.

Không tạo JSON Schema lớn ngay nếu một validator nhỏ đủ dùng. Schema evidence hiện tại chỉ có enum cho hai skill, không biểu diễn trực tiếp A0/A1 hoặc bundle; không giả tên skill để ép vừa schema. Thêm một run record nhỏ cho pilot hoặc mở rộng có chủ đích, giữ tương thích dữ liệu cũ.

## 6. Chấm kết quả và giới hạn kết luận

Chấm từng bài bằng vector checks; nếu cần overall PASS thì đó là phép AND của các yêu cầu bắt buộc đã công bố trước, không dùng trọng số do xem kết quả rồi chọn.

| Run | Task outcome | Preservation/scope | Finding hoặc attribution | Overall | Thời gian/token nếu đo được |
|---|---|---|---|---|---|
| task-id / arm / repeat | pass/fail/not_evaluated | pass/fail/not_evaluated | pass/fail/not_evaluated/not_applicable | pass/fail/not_evaluated | Giá trị thật hoặc unknown |

Việc không sửa gì không được overall PASS ở bài yêu cầu triển khai tính năng. Với review-only, không sửa gì là đúng nhưng còn phải có finding đúng hoặc kết luận sạch đúng tùy bài.

Giữ mẫu số thật và công bố toàn bộ run theo lịch. Đảo thứ tự ba arm giữa các task bằng lịch đã ghi trước để giảm phụ thuộc vào thứ tự chạy. Mỗi run mới không dùng lại hội thoại hoặc output nhánh khác.

Với bộ nhỏ, kết luận phù hợp là: “trên sáu nhiệm vụ đã công bố, cấu hình A2 đạt X/6 trong lần chạy này; khác biệt tập trung ở D1 và R1; chưa đo độ ổn định hoặc các host khác”. Không chuyển thành “tăng chất lượng lập trình X%”, “an toàn hơn mọi baseline” hoặc “không bao giờ phá code”.

Nếu hòa: báo hòa, xem overhead và không ép thêm luật để tạo khác biệt. Nếu thua: phân tích ca thua rồi mở vòng phát triển mới. Nếu thắng: công bố phạm vi và thử lặp trước khi mở rộng claim.

## 7. Các việc nên làm tiếp, theo thứ tự

1. Chọn cùng một host/model và ba cấu hình; ghi revision, quyền và budget.
2. Viết đặc tả D1/D3/R1 và phác trước D2/D4/R2, với check cụ thể và các yêu cầu được agent nhìn thấy.
3. Xây ba fixture đầu cùng verifier và lời giải đối chứng; chưa chạy model lấy điểm cho tới khi validator đã kiểm tra được ca đúng/sai.
4. Chốt commit của skill/task/verifier/protocol; bắt đầu chín lượt đầu.
5. Ghi kết quả như quan sát, không tuning giữa các arm. Mở rộng theo lịch và ngân sách đã chọn.

Đích đến là một bộ thử nhỏ mà người khác hiểu, chạy lại và phản biện được. Máy chấm tự động cho các tiêu chí hữu hạn là khả thi; “100% máy chứng minh mọi khía cạnh chất lượng skill” thì không phải lời hứa nên đưa ra.
