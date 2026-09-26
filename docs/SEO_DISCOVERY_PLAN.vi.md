# Kế hoạch giúp người dùng tìm thấy Repository Engineering Skills

Ngày nghiên cứu: 2026-09-26. Đây là đề xuất dành riêng cho repository này, chưa phải kết quả tăng trưởng đã đo được. Các mẫu bên dưới chưa được áp dụng lên GitHub.

## 1. Hiện trạng đã kiểm tra

- Repository public: `Natchannnn/repository-engineering-skills`.
- GitHub About đã mô tả đúng hai skills, nhưng `topics` đang rỗng, `homepage` chưa có và GitHub Pages chưa bật, theo GitHub API tại thời điểm kiểm tra.
- README đã có lệnh cài qua Skills CLI, hướng dẫn chọn skill và giới hạn benchmark. Đây là nền tảng tốt để người mới quyết định có dùng hay không.
- Những thay đổi đang được review vẫn chưa commit/push. Nội dung local chưa có tác dụng đối với người đọc GitHub.
- Hai truy vấn chính xác về tên chủ repo/tên repository và tên chủ repo trên skills.sh không trả về kết quả trong công cụ tìm kiếm của phiên này. Điều đó **không chứng minh Google chưa index**, cũng không phải phép đo thứ hạng.
- Chưa có dữ liệu Search Console, traffic riêng của repo hoặc số lượt tìm kiếm từ khóa. Thứ tự ưu tiên trong tài liệu là nhận định về độ phù hợp, không phải dự báo lưu lượng.

Ưu tiên trước khi quảng bá installer mới: xử lý lỗi cập nhật giữa chừng, đưa LICENSE vào payload và sửa tuyên bố xác minh quá mức. Chi tiết ở [báo cáo review installer](LOCAL_INSTALLER_REVIEW.vi.md).

## 2. Định vị nên dùng

Người chưa biết tên skill có thể tìm theo công việc: review code với Codex, refactor một diff mà giữ hợp đồng công khai, hoặc tiếp tục phát triển repository qua nhiều phiên. Tên `repo-foundation` và `repo-native-refactor` nên được giải thích bằng các công việc đó.

Đề xuất lấy **code review và scoped refactoring với Codex** làm cửa vào dễ hiểu, rồi giới thiệu Foundation cho xây dựng tính năng và thay đổi hợp đồng. Đây là giả thuyết nội dung cần đo, không phải kết luận rằng nhu cầu refactor lớn hơn nhu cầu foundation.

Giữ nguyên tên repo và hai skill. Việc đổi tên bây giờ tạo thêm công cập nhật lệnh cài, liên kết và tài liệu; chưa có bằng chứng lợi ích đủ lớn để làm.

## 3. GitHub About và topics: có thể áp dụng ngay sau khi chốt bản phát hành

Trên trang repository, mở nút chỉnh sửa cạnh **About**. Dùng description sau:

```text
Agent skills for code review, scoped refactoring, and repository development. Includes Codex installation instructions, evaluation harnesses, and archived examples.
```

Đề xuất tám topics:

```text
agent-skills
codex
code-review
refactoring
ai-coding
developer-tools
software-engineering
testing
```

Topics giúp phân loại và tìm repository trong GitHub. Không có cơ sở để hứa thêm topics sẽ tự nâng thứ hạng Google. [Tài liệu GitHub về topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics).

Chưa thêm tên những agent chưa được thử chỉ để thu hút truy vấn. Để trống Website cho đến khi có trang tài liệu hoạt động. Không cần tạo trang web chỉ để lấp trường này.

## 4. Mẫu mở đầu README

Đây là bản thay thế cho phần giới thiệu, không phải phần cần chèn thêm để lặp lại nội dung hiện có:

```markdown
# Repository Engineering Skills: Code Review and Refactoring for AI Agents

Two agent skills for repository development, code review, and scoped refactoring. The installation guide includes tested Codex project commands using the Skills CLI.

- **repo-foundation** guides project setup, feature work, public contract changes, and work across sessions.
- **repo-native-refactor** reviews code changes and guides scoped cleanup, with attention to existing behavior and repository conventions.

[Install in a Codex project](docs/installation.md) · [Choose a skill](#choosing-a-skill) · [Read the evaluation evidence](docs/evaluation.md)

Evaluation harnesses and historical comparison runs are included. The experiments cover a limited set of tasks and do not establish consistent gains across models or repositories.
```

Khi dùng mẫu này, đổi heading hiện tại `## 2. Choosing Between the Skills` thành `## Choosing a skill` để liên kết `#choosing-a-skill` trỏ đúng. Kiểm tra lại các liên kết cũ đang trỏ tới heading đó.

Thứ tự đọc đề xuất: mô tả ngắn → lệnh cài chính → khi dùng skill nào → thử một việc cụ thể → bằng chứng và giới hạn → đóng góp. Dùng liên kết sang installation để giữ phần đầu gọn; người mới không cần đọc toàn bộ lịch sử audit trước khi thử.

Google khuyến nghị tiêu đề mô tả đúng nội dung, văn bản dễ đọc và liên kết có ý nghĩa; việc lặp nhiều biến thể từ khóa không cần thiết. README heading có ích cho người đọc nhưng không cho bạn toàn quyền điều khiển HTML title hay snippet mà Google hiển thị. [Google SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide).

## 5. Nhóm truy vấn và nội dung cần trả lời

Các cụm dưới đây là giả thuyết truy vấn tiếng Anh, **không có số liệu search volume hoặc keyword difficulty**.

| Nhu cầu | Cụm truy vấn để theo dõi | Nội dung trả lời | Ưu tiên |
|---|---|---|---|
| Tìm skill review cho Codex | `codex code review skill` | README: công dụng, phạm vi đã thử, ví dụ review chỉ đọc | Cao |
| Refactor có giới hạn | `agent skills refactoring` | README và ví dụ diff trước/sau có kiểm tra | Cao |
| Cài và bắt đầu dùng | `install codex skills npx` | installation: yêu cầu môi trường, lệnh cài, cách gọi skill, gỡ cài | Cao |
| Giữ hợp đồng khi sửa code | `refactor code preserve public API` | Một case study về kiểu trả về/caller/test | Vừa |
| Xây tính năng theo quy ước repo | `codex repository development skill` | Ví dụ Foundation trên một tính năng nhỏ | Vừa |
| Tìm đúng dự án | `repo-native-refactor`, `repo-foundation` | Tên nhất quán trong README, thư mục skill và hướng dẫn | Cần có |

Mỗi nội dung phải giải quyết một việc thật. Không tạo hàng chục trang chỉ đổi tên agent hoặc ngôn ngữ. Giữ tài liệu hướng tới người dùng quốc tế bằng tiếng Anh; hướng dẫn tiếng Việt có thể là bản bổ trợ được liên kết rõ.

Không nhồi từ khóa vào `SKILL.md` frontmatter: phần đó phục vụ agent chọn đúng skill. Nếu sửa description, kiểm tra tác động đến routing. Cụm `regression-free refactoring` hiện vẫn có trong description của Refactor; có thể thay bằng `behavior-preserving refactoring with verification` để thể hiện mục tiêu và cách kiểm tra, tránh cách đọc như lời bảo đảm.

## 6. Hai ví dụ có giá trị hơn một trang quảng cáo dài

Đây là **đề xuất thử nghiệm mới**, chưa có kết quả để đưa vào benchmark.

### Ví dụ A: review code mà không tự sửa

- Một repository nhỏ, commit đầu vào được ghi rõ, chứa một thay đổi public return type có caller phụ thuộc.
- Prompt gọi Refactor ở chế độ review chỉ đọc.
- Công bố finding, vị trí code, hệ quả đối với caller và kết quả kiểm tra diff không bị sửa.
- Ghi model, phiên bản skill, prompt, lệnh kiểm tra, kết quả thực tế và điều chưa thử.

### Ví dụ B: thêm tính năng có giới hạn

- Một yêu cầu nhỏ, tiêu chí chấp nhận rõ; gọi Foundation.
- Cho thấy các file đã đổi, lý do đổi, kiểm tra hành vi và phần docs cần đồng bộ.
- Thêm một tình huống không cần abstraction mới để người đọc thấy mức độ tiết chế.

Một demo đơn lẻ chỉ minh họa hành vi. Muốn tuyên bố tốt hơn baseline cần điều kiện đối chứng và nhiều lần chạy; không biến screenshot đẹp thành kết luận hiệu quả tổng quát. Có thể dùng archive hiện có làm ví dụ lịch sử nếu ghi đúng revision và không gán kết quả cho bản mới.

Tên bài đề xuất, chỉ xuất bản sau khi có dữ liệu tương ứng:

- `Review a Python API change with Codex without rewriting the code`
- `Add a repository feature with explicit scope and verification`

Liên kết từ bài tới đúng hướng dẫn cài và bằng chứng. Chia sẻ bài ở cộng đồng phù hợp với quy định nơi đó; ghi rõ mình là tác giả. Lượt từ bài cộng đồng là referral, không tự gọi là Google organic traffic.

## 7. Skills.sh là một kênh tìm thấy riêng

Theo FAQ chính thức, danh mục/leaderboard dựa trên telemetry cài đặt của Skills CLI. Đây không phải quy trình xuất bản một npm package riêng. Các lần thử ở lượt trước đã tắt telemetry, vì vậy không nên trông đợi chúng tạo tín hiệu xuất hiện trên danh mục. Không chạy cài lặp để làm đẹp số đếm. [Skills.sh FAQ](https://skills.sh/docs/faq).

Chưa xác nhận được trang riêng của hai skill trong lần nghiên cứu này: công cụ không mở được các URL ứng viên. Không suy ra chúng chắc chắn không tồn tại, và chưa chèn badge hoặc URL trang skill chưa xác minh vào README.

Khi trang đã xuất hiện, kiểm tra tên, mô tả, repo nguồn và lệnh cài thực tế. Skills.sh có `skills.sh.json` để nhóm các skill trên trang repository; file đó chỉ chỉnh cách trình bày, không thay đổi cài đặt. Với hai skill, chưa cần thêm cấu hình này. [Hướng dẫn tùy chỉnh Skills.sh](https://skills.sh/docs/customize).

## 8. Khi nào cần website tài liệu

Giai đoạn hiện tại: ưu tiên README, installation và một ví dụ thực tế. Nếu có thể duy trì nội dung, dùng GitHub Pages làm website nhỏ gồm trang giới thiệu, hướng dẫn cài và case study; chưa cần framework phức tạp hay mua domain ngay.

Website do bạn kiểm soát giúp cấu hình title, description, canonical và xác minh Search Console theo khả năng hosting. Thêm một file `robots.txt` vào repo không điều khiển crawler đối với trang `github.com/...`; quyền kiểm soát repo file khác quyền kiểm soát website GitHub.

Search Console cung cấp dữ liệu hiển thị, truy vấn và click của property được cấp quyền. Dùng dữ liệu này khi có website đã xác minh; không suy ra CTR Google từ số lượt ghé repository. [Giới thiệu Search Console](https://support.google.com/webmasters/answer/9128668?hl=en), [quyền sở hữu property](https://support.google.com/webmasters/answer/7687615?hl=en).

Không cần ưu tiên `llms.txt`, schema đặc biệt hay mẹo “AI SEO” cho giai đoạn này. Google nói không có yêu cầu tối ưu riêng hay file AI đặc biệt để xuất hiện trong AI Overviews/AI Mode; được index cũng không bảo đảm được hiển thị. [Google: AI features and your website](https://developers.google.com/search/docs/appearance/ai-features).

## 9. Đo lường trong bốn tuần

Đây là lịch làm việc đề xuất, không phải lời hứa có tăng trưởng sau bốn tuần. Không có automation nào được tạo.

| Tuần | Việc làm | Dữ liệu cần lưu |
|---|---|---|
| 1 | Sửa installer; chốt bản public; cập nhật About/topics và mở đầu README | Commit, ngày đổi nội dung, traffic ban đầu |
| 2 | Chạy và viết ví dụ review chỉ đọc; liên kết từ README | Kết quả demo, trang được đọc, phản hồi cài đặt |
| 3 | Viết ví dụ Foundation nếu có dữ liệu; chia sẻ đúng cộng đồng | Nguồn referral, lỗi người dùng gặp, câu hỏi thường gặp |
| 4 | Xem nội dung nào có người đọc và người thử; chọn một điểm để cải thiện | So sánh cùng cửa sổ thời gian; ghi cả dữ liệu thiếu |

Vào **Insights → Traffic** mỗi tuần và lưu dữ liệu để không mất lịch sử ngắn. GitHub hiển thị visitors/full clones trong 14 ngày, cùng nguồn giới thiệu và nội dung phổ biến cho người có quyền phù hợp. [GitHub Traffic](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-traffic-to-a-repository).

Mẫu bảng tự ghi:

```csv
period_start,period_end,commit,content_change,unique_visitors,unique_cloners,top_referrer,search_clicks,search_impressions,installation_issues,notes
```

Để trống số liệu không có quyền truy cập; không điền 0 thay cho “chưa biết”. Ghi riêng ngày tự clone/chạy installer/CI để nhận biết nhiễu. Không cộng các cửa sổ 14 ngày chồng nhau thành tổng tháng. Installs, unique cloners và người dùng sử dụng thành công là các chỉ số khác nhau.

Nếu có Search Console: nhiều impressions nhưng ít click là tín hiệu xem lại tiêu đề và mức phù hợp truy vấn; ít impressions cần xem tình trạng index và nội dung trước. Nếu người đọc tới installation rồi báo lỗi, ưu tiên trải nghiệm cài đặt. Với mẫu nhỏ, chỉ coi biến động là tín hiệu để điều tra, chưa kết luận thay đổi nội dung gây tăng trưởng.

## 10. Thứ tự thực hiện đề xuất

1. Sửa và kiểm tra installer mới; giữ tuyên bố tương ứng bằng chứng.
2. Commit/publish đúng bản đã kiểm tra, rồi xác nhận CI trên chính commit đó.
3. Cập nhật About, tám topics và README opening; thử mọi liên kết/lệnh cài ở góc nhìn người mới.
4. Công bố một ví dụ review có thể tái hiện, sau đó thêm ví dụ Foundation.
5. Kiểm tra hiện diện trên Skills.sh và ghi traffic hằng tuần.
6. Chỉ mở rộng website/nội dung sau khi biết câu hỏi và khó khăn thật của người dùng.

Điểm đáng giới thiệu của dự án là phạm vi công việc rõ và bằng chứng có thể kiểm tra. Tài liệu nên cho người đọc thấy điều đó bằng ví dụ, đồng thời phân biệt điều đã thử với điều còn kỳ vọng.
