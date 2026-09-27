# Review đặc tả pilot D1, D3, R1

**Cập nhật mới nhất — v1.2:** duyệt bắt đầu triển khai D1. Xem mục 8 về hai điểm cần chốt trước D3/R1 và điều kiện trước khi chạy chín lượt. Mục 7 giữ kết quả review v1.1 để truy nguyên.

Ngày: 2026-09-27. Đối tượng: `docs/PLAN_BEHAVIORAL_PILOT_D1_D3_R1.vi.md`. Đây là review thiết kế, chưa thực thi verifier mới vì chưa có implementation trong phạm vi kiểm tra.

**Kết luận: duyệt phạm vi ba bài và cấu trúc thư mục; yêu cầu sửa các hợp đồng dưới đây trước khi viết verifier và chạy lấy điểm.** Các điểm này có thể chỉnh trong đặc tả hiện có, không cần mở rộng thành framework hay thay hai skill.

## 1. Công bố hợp đồng nhiệm vụ trước, giữ kín dữ liệu kiểm tra

Hiện D1 định chấm leading zero, Unicode space, uppercase prefix nhưng prompt chỉ nói “sửa lỗi chuẩn hóa”. Chưa biết phải giữ hay bỏ leading zero, nhận những prefix nào, xử lý input sai bằng giá trị trả về hay exception nào. D3 cũng chưa định nghĩa nguồn dữ liệu, key quý, kiểu số, quý trống, rounding và năm không hợp lệ.

Trước khi xây canonical solution, ghi các hành vi đó vào task hoặc public specification mà cả ba arm đều được đọc. Hidden tests giữ kín input cụ thể và tổ hợp ca biên, không giữ kín yêu cầu bắt buộc. Chỉ chấm yêu cầu đã công bố. Dữ kiện thiếu có thể làm một implementation hợp lý bị chấm sai, lặp lại vấn đề hard gate CP3.

Với D1, chốt bảng input/output và error behavior. Với D3, chốt signature, representation tiền, cách lấy dữ liệu và schema output. Không cần thêm nhiều edge cases ngoài nhu cầu của task.

## 2. D1: AST shape cộng một số test chưa bảo toàn code của user

Vị trí đặc tả: mục D1.B.2, dòng 41. Giữ số câu lệnh/parameters/annotations vẫn cho phép thay hằng số, điều kiện hoặc biểu thức. Một bản sửa sai có thể giữ nguyên shape và vượt qua các input hành vi hiện có.

### Hợp đồng đề xuất

- Lưu hai mốc: `INITIAL_HEAD` của commit gốc và snapshot **trạng thái giao cho agent** sau khi đã thêm hàm/test uncommitted của user và hoàn tất setup. Mốc thứ hai mới chứa công việc cần bảo vệ.
- Lưu exact source của hàm user tại đúng binding/module, kèm decorators/comment thuộc vùng bảo vệ; verifier xác nhận có đúng một định nghĩa top-level tương ứng và source vùng đó không đổi. AST dùng để xác định cấu trúc, không chỉ đếm statements.
- Kiểm tra byte-exact file test uncommitted `tests/test_priority_fee.py`. Nó cũng là công việc của user.
- Chỉ cho phép sửa thân/vùng hàm normalization như task công bố và thêm test ở vị trí đã định. Phần module ngoài vùng được sửa phải giữ nguyên, bao gồm imports, constants và các binding liên quan. Không mở allowlist cả `src/order_service.py` rồi bỏ kiểm tra phần còn lại.
- Chạy kiểm tra hành vi của hàm user trên bản nộp trong tiến trình mới để phát hiện bị shadow hoặc vô hiệu hóa.
- Ghi nhận và kiểm tra HEAD, index, stash nếu task công bố bảo toàn chúng. Chỉ `git status` không đủ để xác định nội dung user ban đầu.

Đây là kiểm tra preservation cho fixture có cấu trúc xác định, không phải chứng minh chống mọi Python code cố tình can thiệp runtime.

**Thêm đối chứng:** sửa hàm user nhưng giữ nguyên số statements và vẫn pass các input thông thường; xóa/sửa test uncommitted; giữ hàm nhưng gán đè tên ở cuối module; sửa source ngoài scope. Thêm một lời giải normalization đúng theo cách khác canonical để tránh verifier ép implementation.

## 3. D3: kiểm tra snapshot test và toàn bộ tập kết quả, không loại test đỏ khỏi phép đo

`git diff INITIAL_HEAD -- tests/test_ledger.py` có ích để phát hiện thay đổi working tree so với commit chỉ định, nhưng chưa phải toàn bộ chính sách bảo vệ test. Ví dụ index có nội dung khác working tree; hoặc test runner/config bị sửa để không thu thập test trong khi file gốc nguyên vẹn.

### Hợp đồng đề xuất

- Hash bytes và kiểm tra tồn tại của các file test gốc; kiểm tra index theo quy tắc cấm staging/commit nếu đã công bố. Giữ runner/config liên quan ngoài quyền sửa của agent.
- Chỉ cho phép bổ sung test trong file mới đã định, ví dụ `tests/test_quarterly_balance.py`. Nếu cấm mọi chỉnh sửa file test cũ thì ghi rõ, không đồng thời cho phép append vào đó.
- Chạy baseline thật trước phiên agent, lưu ID đầy đủ, trạng thái và expected failure signature. Xác nhận baseline có đúng lỗi đã thiết kế; nếu không, run lỗi fixture/environment, chưa được chấm agent.
- Sau phiên, chạy lại đầy đủ original suite, gồm cả test đỏ. Original test không được biến mất khỏi collection, bị skip hoặc xfail để né kết quả.
- Chỉ dung thứ lỗi đã biết ở đúng test và dạng lỗi đã xác định. Nếu cùng test chuyển sang ImportError hoặc cơ chế lỗi khác thì không gọi đó là lỗi cũ. Thêm test độc lập để bảo vệ các hành vi còn lại.
- Nếu lỗi cũ thực sự được sửa mà test không đổi, không tự đánh trượt vì “phải còn đỏ”; xử lý theo scope công bố. Báo cáo vẫn phải phân biệt baseline đã đỏ với trạng thái cuối đã xanh.

Test ID hiện không thống nhất: phần đầu dùng `tests/test_ledger.py::test_historical_leap_year_rounding`, phần verifier dùng tên ngắn. Chọn một dạng canonical, khuyến nghị ID đầy đủ. So tập hợp chính xác sau kiểm tra schema; reject duplicate/unknown IDs thay vì substring matching.

`new_features_status` không được cố định sẵn là `pass` trong yêu cầu. Dùng schema cho phép trạng thái thực tế; verifier tính task success từ tests, không tin báo cáo agent. Thiếu report là output-contract failure; report trung thực về task thất bại vẫn không biến task thành PASS.

Vòng này chỉ chấm **classification accuracy**, không đo “agent đã chứng minh baseline” nếu chưa thu trace/receipt thực thi. Git log ghi sẵn lỗi cũ còn giúp agent đoán đúng ID; đó là thông tin đầu vào, không phải bằng chứng nó chạy baseline.

**Thêm đối chứng:** giữ nguyên test nhưng làm collection rỗng/skip; lỗi mới ở chính test đỏ cũ; report đúng một ID kèm ID sai; report pass trong khi feature fail. Thêm positive control với ID đầy đủ đúng schema và lời giải feature khác canonical.

## 4. R1: bảo toàn trạng thái ban đầu và chấm đầy đủ finding

Vị trí đặc tả: R1.B.1, dòng 108. `git diff HEAD` rỗng vẫn có thể xảy ra sau khi agent sửa rồi commit; hoặc staged content khác trong khi working tree đã được khôi phục.

### Hợp đồng preservation

- Ghi `INITIAL_HEAD` là feature commit lúc giao bài; HEAD phải giữ nguyên.
- Kiểm tra index và working tree theo snapshot ban đầu, cùng manifest bytes của protected files và inventory file mới/mất. Định nghĩa tooling/cache được phép cụ thể.
- Lưu `review_findings.json` **ngoài fixture**, như demo hiện có. Prompt phải nói “không sửa repository; lưu báo cáo vào đường dẫn evidence được cung cấp”, tránh mâu thuẫn giữa “không sửa bất kỳ file nào” và yêu cầu tạo file.
- Chạy runtime oracle trên bản sao riêng sau khi kiểm tra preservation, để việc import/test tạo cache không làm thay đổi bản nộp hoặc kết quả kiểm tra.
- Diễn đạt đúng: bảo toàn trạng thái cuối được kiểm tra; không chứng minh không có intermediate writes rồi undo.

### Hợp đồng finding

Đặc tả hiện chưa kiểm tra `verdict` và `broken_caller_symbol`, dù chúng có trong output schema. Chưa có quy tắc cho một finding đúng kèm nhiều finding sai.

- Chốt schema và enum cho tất cả trường bắt buộc; không substring match.
- Dùng tên nguồn nhất quán, ví dụ qualified symbol của field/class theo fixture. Nếu chấp nhận tên trước/sau rename thì khai báo alias hữu hạn từ trước. Không bắt agent đoán ngầm source_symbol phải là class hay field.
- Kiểm tra cả caller file và symbol. Chuẩn hóa đường dẫn tương đối; reject absolute path, `..`, sai kiểu và thiếu trường.
- Với task có một defect trong phạm vi xác định, kiểm tra tập finding: đúng finding, không duplicate và không có finding ngoài ground truth. Không dừng khi tìm thấy một item đúng.
- Nếu có finding ngoài ground truth có thể là bug thật, đánh dấu cần xem lại chất lượng fixture; nếu fixture sai phải sửa và áp dụng chính sách rerun công bằng, không chấm tùy ý theo arm.
- Oracle phải chứng minh baseline không có breakage và feature branch có đúng breakage mong đợi trên cùng input. Không coi bất kỳ nonzero exit nào, ImportError hay thiếu dependency là xác nhận contract drift.

**Thêm đối chứng:** sửa rồi commit; chỉ sửa index; một finding đúng kèm một finding sai; đúng file nhưng sai caller symbol/verdict; oracle gặp lỗi môi trường thay vì expected exception. Một report đúng khác thứ tự JSON hoặc dùng alias đã công bố phải vẫn PASS.

## 5. Protocol chín lượt: bổ sung thông tin để so sánh công bằng

- Chọn host/version và model identifier thực tế lúc chạy; không dùng ví dụ `codex / gpt-4o` như cấu hình đã xác nhận. Ghi cả hai riêng biệt.
- A0 vẫn nhận task và repository instructions chung. A1 nạp đúng tài liệu Karpathy-inspired được pin URL/SHA, không tự diễn giải lại thành bốn câu. A2 pin skill revision và cách kích hoạt: D1/D3 triển khai theo Foundation, checkpoint theo Refactor; R1 review-only theo Refactor.
- Ghi quyền tool, giới hạn thời gian/token hoặc tool calls nếu host hỗ trợ, cách nhận biết nạp đúng cấu hình, quy tắc timeout/retry trước khi chạy.
- Mỗi run có phiên mới và fixture mới; không chia sẻ output giữa các arm. Loại hoặc ghi rõ ảnh hưởng của global skills/memory ngoài cấu hình dự kiến.
- Đổi thứ tự theo task từ trước, ví dụ D1 A0/A1/A2, D3 A1/A2/A0, R1 A2/A0/A1. Đừng gọi thứ tự đó là random nếu không thực sự randomize.
- Kết quả cần `pass`, `fail`, `not_evaluated` và `not_applicable` phù hợp. Infrastructure/fixture error tách khỏi task failure; timeout theo budget được ghi rõ.
- Không lấy ba bài một lượt làm bằng chứng độ ổn định hoặc hiệu quả tổng quát; công bố toàn bộ chín run theo lịch.

Không cần một số lượng negative controls cố định. Mỗi nhóm checks cần đối chứng cho hành vi thực sự bảo vệ; ưu tiên cả false PASS và false FAIL. Các thử nghiệm trên đây là test verifier offline, không làm tăng số lượt model phải trả phí.

## 6. Thư mục và cách bắt đầu triển khai

`pilots/small-behavioral-pilot/` phù hợp. Nó nằm trong cùng repository, không phải “tách biệt hoàn toàn” hoặc “cô lập tuyệt đối”. Hidden checks không đưa vào context/fixture của agent, nhưng cùng máy và cùng quyền filesystem không tạo security boundary.

Giữ fixture templates, bootstrap, verifier, author tests và protocol trong Git. Run workspaces, logs và báo cáo đặt ngoài checkout hoặc trong thư mục output được ignore riêng. Dùng JSON run record nhỏ nhất đủ lưu revision/cấu hình/check results; không giả tên skill của A0/A1 để ép vào schema hai skill hiện tại.

Trình tự được khuyến nghị:

1. Sửa task contracts và các checks nêu trên trong đặc tả.
2. Viết D1 fixture/verifier cùng positive và negative controls; chạy các controls trước.
3. Làm tương tự D3, rồi R1; chia commit theo bài để dễ review.
4. Đóng băng task/verifier/skill/protocol revision trước chín lượt chấm điểm.

Không yêu cầu thêm hook, parser shell, hệ thống AST đa ngôn ngữ hay một vòng redesign skill để hoàn thành việc này.

## 7. Review bản v1.1 — 2026-09-27

Đã đọc toàn bộ bản v1.1 trên đĩa. Những sửa đổi đạt yêu cầu: phân biệt dirty snapshot với INITIAL_HEAD; bảo vệ test user; thêm kiểm tra hành vi; ID baseline đầy đủ; attribution chỉ là classification accuracy; output ngoài fixture; R1 kiểm tra HEAD/index; so tập finding; alternative positive controls; luân phiên thứ tự arm. Chưa chạy code pilot vì đây vẫn là review đặc tả.

### [P1] Prompt R1 đang cung cấp toàn bộ đáp án

Trong mục R1.A, dòng 153–161, JSON thuộc **Hợp đồng hành vi công bố trong Prompt** ghi chính xác source_file, field bị đổi, caller file, caller symbol và breakage_type. Agent chỉ cần sao chép JSON này; trạng thái repository không đổi và oracle vẫn xác nhận lỗi, nên có thể PASS mà chưa review gì.

Thay JSON trong prompt bằng tên trường với placeholder trung tính. Ví dụ:

```json
[
  {
    "verdict": "defect",
    "source_file": "<relative source path>",
    "source_symbol": "<qualified changed symbol>",
    "broken_caller_file": "<relative caller path>",
    "broken_caller_symbol": "<caller symbol>",
    "breakage_type": "<allowed category>"
  }
]
```

Có thể công bố schema, quy tắc qualified name và enum loại lỗi. Tên cụ thể cùng alias `AccountProfile.tax_identifier`/`AccountProfile.tax_id` chỉ nằm trong ground truth phía evaluator. Prompt yêu cầu tự suy ra các giá trị từ diff. Không cho agent đọc toàn bộ tài liệu thiết kế hoặc README có đáp án.

Thêm control sao chép nguyên mẫu prompt nhưng không giải bài: phải FAIL. Kiểm tra prompt cuối cùng thực sự gửi cho cả ba arm không chứa expected finding.

### [P2] D1 cần cho phép độ dài hàm thay đổi và file test được bổ sung

Dòng 66 dùng “line range” nhưng chưa nói đó là tọa độ ở snapshot hay bản nộp. Nếu dùng số dòng cũ để so bản mới, lời giải đúng thêm vài dòng trong normalization có thể bị chấm thành thay đổi ngoài scope. Dòng 67 nói mọi file khác không đổi, mâu thuẫn với quyền tạo `tests/test_order_normalization.py` trong prompt.

Chốt thuật toán ở mức hợp đồng: xác định độc lập đúng một hàm normalization trong hai bản; giữ signature/decorators ngoài vùng cho phép; thay riêng body được phép sửa bằng sentinel rồi so phần source còn lại. Không dùng fixed line offsets của snapshot để cắt bản nộp. Phần hàm user được bảo vệ phải có đúng một binding top-level; AST/source handling cần thống nhất chính sách newline đã công bố.

Chốt allowlist: body normalization được sửa; file test normalization mới được tạo; protected source và user test giữ nguyên; HEAD/index giữ nguyên. Thêm positive control với thân hàm dài hơn baseline và test mới để bắt false FAIL. Alternative regex không được buộc thêm import ngoài scope: fixture có sẵn import cần thiết hoặc lời giải import bên trong body được phép.

### [P2] D3 vẫn thiếu định nghĩa nguồn dữ liệu và phép tổng hợp

Signature không có tham số giao dịch và đặc tả chưa chỉ rõ đọc giao dịch từ đâu. Cũng chưa phân biệt tổng riêng của từng quý với số dư lũy kế đến cuối quý, và làm tròn từng giao dịch hay sau khi cộng.

Trước khi viết hidden tests, thêm public fixture specification xác định hàm/nguồn dữ liệu, schema ngày và amount, phép tổng hợp, thời điểm rounding và quy tắc input year. Chốt cách xử lý bool vì Python coi bool là subclass của int; không để evaluator tự thêm một cách diễn giải sau khi xem bài nộp. Không cần mở rộng edge cases ngoài phạm vi bài.

### [P2] D3 vẫn bắt test cũ phải tiếp tục đỏ

Dòng 111 bắt test baseline thất bại với signature gốc; một thay đổi hợp lệ có thể làm nó PASS mà không sửa test. Cần chọn chính sách công khai trước: khuyến nghị cho phép PASS nếu thay đổi nằm trong scope, hoặc FAIL đúng signature đã biết; các failure khác vẫn bị chặn. Nếu thực sự không cho sửa bug cũ, công bố phạm vi đó rõ trong task và kiểm tra scope thay vì chỉ suy từ việc test chuyển xanh.

`baseline_failures` vẫn là tập lỗi ở baseline, không phải tập lỗi còn lại ở cuối. Thêm positive control cho test cũ chuyển PASS hợp lệ nếu chọn chính sách cho phép, và chốt failure signature là exception type + message chuẩn hóa chứ không phải toàn traceback chứa đường dẫn/số dòng.

### Hoàn thiện checklist triển khai, không cần vòng redesign

- R1 phải có protected byte manifest/inventory như review trước; Git diffs không thay thế được kiểm tra bytes. Tạo baseline sau setup theo quy trình và xử lý `.agents/`, lockfile, cache theo chính sách cụ thể, tránh tái xuất hiện lỗi installer làm bẩn fixture.
- Preflight oracle xác nhận baseline hoạt động và feature branch có đúng breakage trên cùng input. Lỗi môi trường tách khỏi lỗi agent; kiểm tra preservation trước khi chạy oracle trên bản sao.
- Protocol phải ghi phiên mới cho mỗi run, revision/cấu hình thực tế, giá trị budget và retry policy trước chín lượt. Model trong tài liệu là placeholder, chưa phải cấu hình đã xác nhận. Những mục này có thể hoàn thiện trong PROTOCOL.md trước khi chạy điểm, không cản viết fixture.

**Điều kiện triển khai:** sửa phần prompt lộ đáp án và chốt bốn hợp đồng trên ngay trong đặc tả. Sau đó có thể viết D1 → D3 → R1 theo kế hoạch; không cần bổ sung bài, đổi tên skill hoặc xây hạ tầng mới. Duyệt thiết kế sau khi sửa không thay thế review implementation và chạy các controls.

## 8. Review bản v1.2 — duyệt bắt đầu D1

Đã đọc toàn bộ v1.2 trên đĩa. R1 đã bỏ expected finding khỏi prompt; D1 đã quy định sentinel ở body, cho phép file test mới và có positive control thân hàm dài; D3 đã công bố nguồn dữ liệu, net total, rounding, bool handling và cho phép test cũ chuyển PASS trong scope.

**Duyệt triển khai D1 ngay theo phạm vi hiện tại.** Không yêu cầu một vòng viết lại toàn bộ kế hoạch. Đây là duyệt thiết kế để viết fixture/verifier, chưa xác nhận implementation hoặc phê duyệt chạy benchmark lấy điểm.

### Lưu ý thực hiện D1

AST dùng xác định vùng body; phần source ngoài vùng đó cần so theo source đã chuẩn hóa newline như hợp đồng. Không thay bằng `ast.dump`/`ast.unparse` rồi gọi là bảo toàn source, vì cách đó có thể làm mất khác biệt comment/formatting. Yêu cầu đúng một định nghĩa top-level của mỗi hàm mục tiêu; dùng các controls đã chốt để xác nhận hành vi. Đây là chi tiết triển khai của yêu cầu hiện tại, không mở rộng tính năng.

### Chốt khi tới D3, trước khi chạy lấy điểm

Prompt D3 đang đưa chính ID lỗi baseline vào ví dụ định dạng: `tests/test_ledger.py::test_historical_leap_year_rounding`, đồng thời nói tên lỗi leap year. Điều này làm phần classification accuracy có thể đạt bằng cách chép đáp án từ đề.

Thay ví dụ bằng `<relative_test_file>::<test_name>`, và chỉ yêu cầu phân loại lỗi quan sát được mà không chỉ tên test đỏ. Expected ID vẫn ở evaluator; test/source thực tế vẫn để agent điều tra. Nếu cố ý giữ ID trong đề thì chỉ được diễn giải phép đo đó là tuân thủ báo cáo một lỗi đã được tiết lộ, không phải khả năng tự phân loại lỗi baseline.

### Chốt khi tới R1, trước khi chạy lấy điểm

Prompt cho chọn `contract_drift | signature_changed | removed_symbol | type_mismatch`, nhưng verifier chỉ nhận `contract_drift`. Với field bị đổi tên, `removed_symbol` có thể là một mô tả hợp lý. Cần định nghĩa các category đủ rõ hoặc khai báo trước tập nhãn tương đương được chấp nhận cho fixture. Không đánh trượt chỉ vì thuật ngữ hợp lý khác trong enum do chính prompt cho phép. Thêm positive control tương ứng nếu nhận nhiều nhãn.

### Trước chín lượt agent

Đóng băng protocol thực tế: host/model, revision ba cấu hình, budget, retry policy, phiên mới từng run và phạm vi global instructions. Chạy các positive/negative controls của từng verifier trước. Không cần làm xong những mục vận hành này để bắt đầu code D1.
