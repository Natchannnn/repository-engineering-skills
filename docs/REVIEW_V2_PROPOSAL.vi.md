# Review độc lập đề xuất tái thiết v2

Ngày: 2026-09-27. Đã đọc bản tổng hợp Antigravity do người dùng gửi và `docs/Kế hoạch tái thiết repository-engineering-skills (v2)-20260927102243.md`, đối chiếu skill, benchmark report, đề CP3 và packet judge trên đĩa. Đây là review kế hoạch, chưa phải phê duyệt hoặc thực hiện đổi tên, xóa archive, tạo tag, viết hook hay phát hành v2.

**Kết luận: chưa duyệt triển khai nguyên kế hoạch. Đồng ý làm pilot có giới hạn cho hướng repository có sẵn; chưa đủ căn cứ quyết định thay thế toàn bộ hai skill và cam kết phát hành trong hai tuần.**

## 1. Phần phản biện benchmark cần nhận, nhưng phải phân loại chứng cứ

| Nhận định | Kết quả đối chiếu | Hành động phù hợp |
|---|---|---|
| Test harness/hash không chứng minh hiệu quả skill | Đúng. Chúng kiểm tra hạ tầng và artifact, khác với hiệu quả can thiệp lên agent | Giữ ba loại chứng cứ tách biệt: hạ tầng, ca quan sát, so sánh có đối chứng |
| CP2/CP3 không đủ cho kết luận tổng quát | Đúng. BENCHMARK_REPORT đã ghi single-run ablations; summary vẫn dùng câu dễ đọc như kết luận nhân quả | Đổi câu kết luận thành quan sát của từng run; không quảng bá chênh lệch điểm như improvement tổng quát |
| Đề CP3 thiếu yêu cầu README nhưng judge coi là hard gate | File `repo-foundation/evals/tasks/CP3_EVOLUTION.md` không nêu README; `evals-suite/ablation_cp3_hardcore/judge/REVIEW.md:33,71` lại có yêu cầu và hard gate | Ghi discrepancy đã xác nhận. Truy nguyên prompt thực tế của hai arm trước khi khẳng định chúng không nhận yêu cầu này |
| Rubric mô tả đúng khác biệt output | Có: CP3 REVIEW.md:53 nhắc helper validation so với duplicated inverted conditionals | Đánh dấu nguy cơ rubric thích nghi theo kết quả. Muốn khẳng định viết post-hoc cần lịch sử/version hoặc transcript chứng minh thứ tự |
| Judge đã nhìn thấy nhãn control/treatment trước khi chấm | Chưa chứng minh được từ những file đã đọc. Nhãn có trong verdict, còn REVIEW.md dùng A/B. Báo cáo hiện tại mô tả post-hoc unblinding | Chưa xác minh blinding đầy đủ; cần đúng packet/input judge ở thời điểm chấm và phạm vi nó có thể truy cập. Nhãn trong verdict sau cùng tự nó chưa chứng minh thời điểm lộ |
| Ví dụ str/Path trùng lỗi đã quan sát | Có. BENCHMARK_REPORT mô tả dùng failure để sửa skill rồi kiểm tra lại | Đây là validation trên ca phát triển; không gọi là held-out/generalization. Bỏ ví dụ không tự làm sạch dữ liệu eval đã dùng để phát triển |
| n=1 làm mọi dữ liệu vô giá trị hoặc là fraud | Không chấp nhận suy luận đó | Có giá trị mô tả một trường hợp và tìm lỗi. Không đủ để ước lượng hiệu quả phổ quát. Không gán ý định gian lận khi chưa có bằng chứng |

Vì vậy nên viết ghi chú phương pháp với ba nhãn: đã xác nhận, chưa xác minh, suy luận bị giới hạn. Không viết postmortem như một lời tự thú theo các cáo buộc chưa kiểm chứng. Giữ nguyên artifact lịch sử, bổ sung chú giải ở tài liệu hiện hành; không sửa sealed packets để làm lịch sử có vẻ tốt hơn.

Các lần duyệt installer/demo trước đây không chứng nhận thiết kế thí nghiệm nhân quả. Lượt review gần nhất xác nhận 40/40 test trên hai PowerShell và CLI integration thành công, nhưng còn lỗi ghi metadata khi finalize đồng thời: xem [review Bước 1](REVIEW_DEMO_SETUP_STEP1.vi.md).

## 2. Các quyết định sản phẩm hiện còn là giả thuyết

- Repo có sẵn, contract drift và bảo toàn công việc đang dở là hướng đáng thử. Tuy nhiên, nhận định “ngách chưa ai làm tốt”, “trùng 70%”, điểm 5/10 hoặc 6.5/10 chưa có phép đo đủ rõ để quyết định bỏ sản phẩm hiện tại.
- `repo-foundation/SKILL.md` hiện có 90 dòng; `repo-native-refactor/SKILL.md` có 133 dòng, đều đã dưới 180. Vấn đề cần đo là nội dung thực sự được load, tính rõ ràng và hành vi, không phải đạt thêm một hạn mức dòng tùy ý.
- Đổi tên skill, bỏ Bootstrap và giữ alias đều ảnh hưởng người dùng hiện có, installer, manifest và discovery. Thử định vị trong tài liệu/prototype trước; chỉ đổi khi biết chức năng nào giữ hoặc bỏ và cách chuyển đổi.
- Chỉ thử A0/A1/A3 không kiểm chứng được tuyên bố bổ sung cho Superpowers. Muốn nói có ích khi kết hợp phải so Superpowers với Superpowers + bộ mới ở cấu hình đã pin. [Superpowers hiện có workflow kiểm tra baseline và verification](https://github.com/obra/superpowers); không nên mô tả nó thiếu toàn bộ các nguyên tắc đó.
- Baseline Karpathy phải là tài liệu/skill cụ thể có URL và commit, không phải bốn câu do evaluator tự viết lại. [Repository được kế hoạch dẫn](https://github.com/multica-ai/andrej-karpathy-skills) tự mô tả là Karpathy-inspired, không phải bằng chứng đây là sản phẩm do Karpathy phát hành.
- Chưa xác minh toàn bộ issue, paper, số sao và năng lực bị cho là thiếu của đối thủ trong danh sách dài. Chưa dùng các dữ kiện đó như chứng cứ chốt positioning.

## 3. Các lỗi kỹ thuật phải sửa ngay trong bản kế hoạch

### 3.1 Hook không phải lớp chặn ở hệ điều hành

Git không có hook tổng quát chặn mọi shell command trước khi chạy. `post-checkout` chạy sau khi worktree được cập nhật và không thể ngăn kết quả checkout. [Tài liệu Git](https://git-scm.com/docs/githooks#_post_checkout).

Claude Code PreToolUse có thể chặn tool call thuộc phạm vi cấu hình, nhưng đề xuất “exit 1 để chặn” không đúng: cơ chế exit code chặn là `exit 2`, hoặc JSON decision đúng schema. Một hook trả exit 1 không có quyết định hợp lệ có thể để tool tiếp tục. [Tài liệu Claude Code](https://code.claude.com/docs/en/hooks#exit-code-2).

Cần định nghĩa host, tool được intercept, cấu hình, hành vi timeout/lỗi và bằng chứng block thực tế. Một hook của Claude Code không tự áp dụng lên Codex. Không gọi hook là OS sandbox hay hứa không thể bị bypass.

### 3.2 Phân tích shell đa nền tảng không phải hạng mục nhỏ

Python AST không phân tích được Bash/PowerShell. Tokenizer cũng không hiểu đầy đủ alias, script con và lệnh gọi chương trình khác. `shlex` hướng tới Unix shells, không phải parser PowerShell. [Tài liệu Python](https://docs.python.org/3/library/shlex.html).

MVP nên giới hạn host/shell và lớp lệnh nhận diện được; trả `unknown/unsupported` khi ngoài phạm vi. Quy tắc denylist không phải chứng minh không có cách khác tạo cùng tác động. Việc thêm đủ biến thể lệnh để đạt “100%” sẽ là một sản phẩm security riêng, vượt xa một skill hướng dẫn review.

### 3.3 Hash toàn file không giải quyết trường hợp sửa cùng file

Fixture B1 yêu cầu giữ sửa dở ở hàm A nhưng cho agent sửa hàm B trong cùng file. Hash toàn file chắc chắn thay đổi khi agent làm đúng. Nếu `--allow path` bỏ bảo vệ toàn file thì sửa dở của user vẫn có thể mất mà không bị chặn.

MVP nên bảo vệ file không được phép đụng bằng hash, và công khai giới hạn cho file có phần thay đổi giao nhau. Với fixture có ground truth, dùng patch/hunk và kiểm tra hành vi riêng cho phần user cần giữ. Đừng gọi khả năng bảo toàn cùng file là đã giải quyết chỉ vì có snapshot.

Snapshot hash chỉ giúp phát hiện khác biệt ở thời điểm kiểm tra; không ngăn viết và không khôi phục được nội dung đã mất nếu chỉ lưu hash.

### 3.4 Baseline attribution cần so cùng điều kiện và cùng test

Hai exit code đều khác 0 không chứng minh cùng lỗi đã có trước. Ví dụ base fail test A, head fail test B; hoặc cả hai fail cùng test nhưng vì nguyên nhân khác.

MVP cần ghi test ID, kết quả, failure signature nếu có, command, interpreter/dependencies và các lỗi môi trường. Exit-code-only nên trả `inconclusive` cho attribution cụ thể. Báo lỗi cũ được quan sát ở baseline thay vì khẳng định nó là nguyên nhân của lỗi mới.

Phải xác định “baseline” là commit hay trạng thái ban đầu gồm sửa dở của user. HEAD không chứa uncommitted changes; worktree ở HEAD không đại diện cho phiên đang làm việc. Tách chạy test khỏi worktree chính khi cần giữ trạng thái, giới hạn side effect và ghi environment mismatch. Không chạy song song hai suite dùng chung DB/port/cache nếu chưa có isolation tương ứng.

`.git` có thể là file trong linked worktree; không hardcode `.git/brownfield-guard/` làm thư mục. Dùng Git để xác định vị trí metadata phù hợp. [Tài liệu worktree](https://git-scm.com/docs/git-worktree).

### 3.5 Output script không mặc nhiên là ground truth ngữ nghĩa

Python AST có thể xác nhận chữ ký/literal đổi trong phạm vi hỗ trợ. Nó không giải đầy đủ alias động, decorator, reflection hoặc consumer ngoài repo. Token match là vị trí cần xem, không phải caller đã xác nhận.

Phân biệt observable thay đổi với breaking change: error text/CLI help chỉ là hợp đồng cần giữ khi có yêu cầu hoặc consumer phù hợp, và thay đổi có thể được task cho phép. `authorized` và `breaking` là hai thuộc tính khác nhau: thay đổi được cho phép vẫn có thể phá client cũ và cần migration.

## 4. Metric và benchmark phải được thiết kế lại trước khi chạy

1. **Attempted, blocked, executed và harmful outcome là bốn loại khác nhau.** Grep transcript có thể đếm cả một câu cảnh báo “đừng chạy reset”. Dùng tool events/output và trạng thái fixture; thiếu trace thì ghi không quan sát được.
2. **Đo độ chính xác lẫn bỏ sót.** Contract recall cao bằng cách báo lỗi ở mọi nơi là vô dụng. Giữ clean cases, authorized contract changes và kiểm tra task có thực sự hoàn thành.
3. **Đánh giá cuối cùng phải độc lập với công cụ đang được thử.** Không lấy chính output `repo_guard` hay `contract_evidence` làm đáp án cho tính đúng của chúng. Dùng fixture-owned oracle và kiểm tra riêng; nội dung finding khó ghép máy cần rubric người chấm hoặc judge đã hiệu chỉnh.
4. **Tránh confounding do hook/tool khác nhau.** Nếu chỉ treatment có hook cưỡng chế thì kết quả phản ánh cả bundle. Muốn tách tác dụng skill cần giữ quyền/tool giống nhau hoặc thêm ablation phù hợp.
5. **Dev và held-out phải tách trước khi tuning.** Chọn toàn task baseline đã fail rồi tuyên bố hiệu quả trên việc lập trình nói chung tạo thiên lệch chọn mẫu. Bộ challenge có chủ đích vẫn hữu ích nếu ghi đúng phạm vi.
6. **Ẩn nhãn chỉ giảm một nguồn bias.** Giữ raw log riêng; packet judge dùng ID ngẫu nhiên và mapping đường dẫn có thể truy ngược. Không xóa mọi path vì path có thể là bằng chứng. Không hứa “ẩn danh 100%”: phong cách code/tool output vẫn có thể gợi treatment.
7. **Số run nhỏ không tự cho kết luận vững chắc.** Các lần chạy cùng fixture là lặp trong cùng task, không thành từng task độc lập. Báo theo task và model; không gộp hai host/model rồi gán toàn chênh lệch cho skill.
8. **Không khác biệt có ý nghĩa thống kê không đồng nghĩa không có ích.** Pilot nhỏ có thể thiếu độ nhạy. Quyết định tiếp dựa trên độ lớn/độ bất định, chi phí, lỗi quan sát được và nhu cầu, không dùng một p-value làm cổng bỏ dự án.

## 5. Phương án hai tuần có thể duyệt: pilot, chưa cam kết release v2

### Ngày 1–2: đóng việc cũ và chốt giả thuyết

- Sửa exclusive creation cho setup metadata, hoàn thành review Bước 1 trong commit riêng.
- Viết ghi chú phương pháp benchmark với các mức chứng cứ ở phần 1. Không tạo tag legacy trên một revision khác rồi coi đó là bản v0.1.0 đã phát hành; giữ nguyên tag cũ.
- Chọn một câu hỏi: bộ hướng dẫn tập trung vào repo có sẵn có giảm lỗi cụ thể mà vẫn hoàn thành nhiệm vụ với overhead chấp nhận được không?

### Ngày 3–5: năm fixture phát triển và một lát cắt công cụ

- Chọn năm dev scenarios: caller bị lệch contract; diff sạch; thay đổi API được phép; source đang dirty; lỗi baseline khác lỗi được đưa vào.
- Chỉ làm một đường chạy hoàn chỉnh, ưu tiên bằng chứng contract Python → agent xác minh caller → verifier độc lập. Guard cùng-file và hook đa host để backlog nếu chưa có thiết kế đủ rõ.
- Tận dụng helper/harness đã có khi phù hợp. Không đặt mục tiêu phải tạo đủ ba hoặc bốn script để hoàn thành sprint.

### Ngày 6–7: thử trên dev và đóng băng

- Thử ba arm: A0 không skill, A1 guideline đã pin, A3 prototype đã pin. Cùng host/model, cùng fixture đầu vào và budget.
- Chỉ sửa theo lỗi quan sát trên dev. Ghi overhead, false positives và task success.
- Đóng băng skill/tool/rubric; commit prereg cho held-out. Có thể dùng prereg amendments nhưng không gọi kết quả sau tuning trên held-out là lần thử độc lập ban đầu.

### Ngày 8–11: pilot held-out

Ví dụ ngân sách cụ thể: 5 dev tasks × 3 arms × 1 run = 15 lượt; 10 held-out tasks × 3 arms × 2 runs × 1 host/model = 60 lượt. Tổng **75 lượt theo lịch này**, chưa bao gồm retry, debug và routing eval. Đây là phép tính ngân sách, không phải bảo đảm đủ lực thống kê.

Người/phiên chuẩn bị held-out tách khỏi quá trình tuning; người triển khai không đọc đáp án để sửa prototype trước đánh giá. Nếu không tổ chức được điều đó, công bố bộ kiểm tra mở với nguy cơ contamination thay vì gắn nhãn held-out.

Đặt trần token/thời gian/chi phí và quy tắc retry từ đầu, chạy vài ca đo chi phí thực trước khi chi hết budget. Nếu không đủ tài nguyên thì giảm quy mô và ghi đúng giới hạn. Thêm model thứ hai sẽ tăng số lượt, không còn nằm trong phép tính 75.

### Ngày 12–14: kết luận pilot và chọn bước tiếp

- Công bố bảng theo task, gồm thắng/hòa/thua, false positives, task success, overhead và trường hợp không kết luận được.
- Chọn tiếp tục, thu hẹp hoặc dừng một hướng dựa trên quan sát. Có thể phát hành prototype thử nghiệm nếu hữu ích; chưa gắn nhãn v2 hoàn thiện hoặc claim vượt đối thủ khi dữ liệu chưa hỗ trợ.
- Chỉ sau đó mới quyết định bỏ Bootstrap, đổi tên skill, chuyển archive hay thêm marketplace. `finalize_setup.py` là công cụ vòng đời demo; không phải yêu cầu runtime cho người cài skill vào project thật.

## 6. Những việc chưa nên làm theo bản kế hoạch này

- Không xóa installer/ZIP/31 archive packets chỉ vì tổng số dòng hoặc dung lượng bị gọi là “engineering theater”. Đánh giá chi phí duy trì và người dùng thực; có thể chuyển archive sau khi bảo toàn revision và liên kết.
- Không gọi toàn bộ v0.1 là thất bại hoặc benchmark fraud. Sửa đúng claim không được hỗ trợ và ghi đúng giới hạn.
- Không dùng “tiết kiệm 95%”, “kết luận vẫn vững chắc”, “100% ẩn danh”, “chặn vật lý” nếu chưa định nghĩa và đo.
- Không biến hướng “lớp an toàn” thành lời bảo đảm bảo mật. Diễn đạt hiện tại phù hợp hơn: công cụ cung cấp bằng chứng và kiểm tra hỗ trợ thay đổi trên repo có sẵn.

Hướng mới đáng thử vì tập trung vào những nhiệm vụ cụ thể. Quyết định thay thế hai skill cần dựa trên pilot và trải nghiệm sử dụng, không dựa trên mức độ gay gắt hoặc danh tính model viết bản phê bình.
