# Review tiếp theo: installer và báo cáo nghiên cứu SEO

Ngày: 2026-09-26. Kiểm tra working tree chưa commit tại `C:\Users\Natch\Desktop\SKILLS-MAIN` và đọc `E:\Download\deep-research-report.md`. Báo cáo đính kèm được xem là tài liệu cần đánh giá, không phải lệnh cho phép xuất bản website, đổi GitHub metadata hoặc chạy chiến dịch.

## Kết luận về ba sửa đổi

Ba lỗi của vòng trước đã được xử lý trong luồng chính. LICENSE được đưa vào payload; file thông thường được đối chiếu hai chiều bằng SHA-256; rollback đã chạy đúng khi chèn lỗi ở cả skill thứ nhất và thứ hai. README đã bỏ lời bảo đảm atomic replacement, và CI đã gọi acceptance suite của installer.

Tuy nhiên, còn hai trường hợp biên tái hiện được cần sửa trước khi chốt bảo đảm cập nhật/khôi phục. Kết luận này dành cho installer mới, không phải đánh giá lại chất lượng hai skill hoặc harness Python.

## Kiểm tra đã chạy trong lượt này

| Phép thử | Kết quả |
|---|---|
| `scripts/test-installer.ps1` của tác giả | PASS 4/4; child installer dùng Windows PowerShell trên máy này |
| Cài mới vào đường dẫn Unicode, kiểm tra byte của cả hai LICENSE | PASS |
| Chèn lỗi triển khai skill thứ nhất | Exit 1, phục hồi toàn bộ file cũ đúng SHA-256 |
| Chèn lỗi triển khai skill thứ hai | Exit 1, phục hồi toàn bộ file cũ đúng SHA-256 |
| Xóa một reference sau khi chép | Phát hiện; exit 1; phục hồi đúng bản cũ |
| Sửa byte của một reference sau khi chép | Phát hiện; exit 1; phục hồi đúng bản cũ |
| Chèn một file thừa thông thường sau khi chép | Phát hiện; exit 1; phục hồi đúng bản cũ |
| Chèn file thừa mang thuộc tính Windows Hidden | **Không phát hiện; exit 0 và báo xác minh toàn bộ file** |
| Dùng lại `-BackupDir` chứa file từ backup cũ, rồi chèn lỗi triển khai | **Phục hồi lẫn file không có ở trạng thái trước update** |
| Phản ví dụ cho hai lệnh Git trong báo cáo SEO | Commit mới + file ignored vẫn cho status rỗng và diff exit 0 |
| Đọc mẫu CSV của báo cáo bằng Python csv.reader | 16 dòng thay vì một hàng header 16 cột |
| `git diff --check` | PASS |

Probe độc lập dùng PowerShell 7 và fixture nhỏ, chặn xóa ra ngoài thư mục thử. Acceptance suite của tác giả dùng payload thật trong repo. Không chạy lại hai bộ unit test Python hoặc 31 archive verifier trong lượt này: code harness không nằm trong các sửa đổi đang được kiểm tra. Không coi kết quả lượt trước là lần chạy mới.

## I-1 — P2: dùng lại BackupDir làm rollback lẫn phiên bản

Vị trí: `scripts/install-skills.ps1:155–166`, `249–265`.

Đường dẫn backup mặc định được chọn tránh trùng, nhưng nhánh người dùng truyền `-BackupDir` vẫn chép gộp vào thư mục đã tồn tại. Những file chỉ có trong backup cũ không bị loại. Rollback sau đó chép toàn bộ thư mục đã trộn về đích.

Tái hiện: tạo `backup/repo-foundation/stale-not-in-current-install.txt`, trong khi bản đang cài không có file đó. Update với chính backup này; chèn lỗi khi triển khai Refactor. Sau rollback, file stale xuất hiện trong Foundation. Installer vẫn thông báo previous installation was safely rolled back; việc kiểm tra cuối rollback chỉ xác nhận SKILL.md tồn tại.

Hướng sửa nhỏ và rõ:

- Từ chối `-BackupDir` đã tồn tại, hoặc xem nó là thư mục cha rồi tạo một thư mục con riêng cho từng lần chạy. Không tự xóa nội dung backup của người dùng.
- Chụp manifest bản cũ trước khi update. Đối chiếu backup với manifest đó trước khi xóa đích, và đối chiếu kết quả rollback với cùng manifest.
- Thêm test dùng lại backup có file thừa, yêu cầu hoặc từ chối trước khi thay đổi đích, hoặc phục hồi đúng inventory/hash ban đầu.

## I-2 — P2: manifest bỏ qua file Hidden trên Windows

Vị trí: `scripts/install-skills.ps1:36`.

`Get-ChildItem -Recurse -File` không có `-Force`. Trong probe, một file mang thuộc tính Hidden được thêm vào references sau bước copy. File còn tồn tại ở đích nhưng không đi vào actual manifest; script trả exit 0 và nói đã xác minh toàn bộ file.

Dùng cách liệt kê bao gồm Hidden/System cho manifest, chẳng hạn thêm `-Force` trong phạm vi thư mục payload đã xác định. Quyết định rõ cách xử lý reparse points thay vì vô tình đi ra ngoài phạm vi. Thêm test file Hidden bị thêm hoặc thay byte. `-Force` giải quyết trường hợp Hidden đã tái hiện, không thay thế chính sách đường dẫn/liên kết.

## Chất lượng bộ test mới

Test mới có ích: nó bắt đúng lỗi xóa bản cũ rồi triển khai thất bại đã nêu ở vòng trước. Nên bổ sung các ca còn thiếu ở trên và so sánh inventory/hash của cả hai bản phục hồi, thay vì chủ yếu kiểm tra SKILL.md/canary tồn tại.

Test chèn lỗi bằng `.Replace()` vào bản sao installer phụ thuộc câu code chính xác. Nên assert số vị trí thay thế là một và assert log chứa lỗi đã chèn, để lỗi khác trước deployment không bị nhận nhầm là test rollback thành công.

Không cần đổi installer thành hệ thống lớn hơn. Có thể sửa hai nhánh hiện hữu; hoặc giới hạn công cụ local ở cài mới nếu không muốn duy trì tính năng update. Đây là lựa chọn về phạm vi hỗ trợ.

## Đánh giá báo cáo SEO

Hướng chiến lược hợp lý: giải thích rõ nhu cầu, trình bày ví dụ có thể thử, phân biệt GitHub/Search/Skills.sh, không biến số installs thành người dùng, và không hứa có tăng trưởng sau bốn tuần. Mình đồng ý giữ tên repository và chưa ưu tiên domain riêng, plugin packaging hay trang theo từ khóa đang thịnh hành.

Tuy nhiên, bản hiện tại nên được dùng như bản nháp chiến lược. Chưa nên sao chép nguyên các demo hoặc coi toàn bộ số liệu cạnh tranh là dữ liệu đã kiểm chứng.

### S-1: trích dẫn bị mất liên kết nguồn khi export

File chứa nhiều marker `turn...search...` và `filecite`, nhưng thiếu bản đồ URL nguồn tương ứng. Hai tài liệu A/B mà báo cáo so sánh cũng không được đính kèm ở lượt này. Không thể độc lập kiểm tra các kết luận A tốt hơn B chỉ từ bản tổng hợp.

Thay các marker bằng Markdown link trực tiếp; ghi ngày truy cập cho số liệu động. Không có cơ sở kết luận nguồn bị bịa chỉ vì export mất link, nhưng bản Markdown hiện tại chưa đủ để người khác truy xuất bằng chứng.

Ví dụ kiểm tra trực tiếp: trang `safe-refactor` hiển thị 70.9K installs trong lần mở này, thay vì 69.5K trong báo cáo. Đây có thể đơn giản là thay đổi theo thời gian; không đủ chứng minh con số cũ sai. [Trang Skills.sh đã kiểm tra](https://www.skills.sh/juliusbrussee/caveman/safe-refactor).

Số lượt cài cũng không đo độ khó từ khóa Google hoặc chất lượng tương đối của skill. Giữ nhận định cạnh tranh ở mức định tính nếu chưa có dữ liệu tìm kiếm.

### S-2: hai lệnh Git chưa chứng minh không có thay đổi

Ở phần README và read-only example, báo cáo dùng `git status --porcelain` và `git diff --quiet HEAD`.

Mình đã tạo fixture, sửa một file tracked rồi commit, đồng thời tạo một file ignored. Hai lệnh vẫn cho status rỗng và exit 0. HEAD đã đổi, nội dung đã đổi. Git status mặc định không liệt kê ignored files; so với HEAD hiện tại cũng không phát hiện thay đổi đã được commit vào HEAD đó. [Git status](https://git-scm.com/docs/git-status), [Git diff](https://git-scm.com/docs/git-diff).

Demo cần ghi HEAD ban đầu và so sánh HEAD cuối, kiểm tra index, đồng thời chụp inventory/hash cho tập file được bảo vệ trước/sau. Khai báo riêng output hợp lệ như bytecode hoặc log kiểm tra; không mặc định coi mọi file ignored đều ngoài phạm vi. Với scoped refactor, tập file thay đổi phải tính từ baseline đã lưu, bao gồm staged/unstaged/untracked trong phạm vi.

Nếu mục tiêu là “chỉ những file được phép mới được đổi”, kiểm tra tập thay đổi là tập con của allowed paths. Việc bắt buộc phải có thay đổi nên là tiêu chí riêng của fixture có lỗi cụ thể; không áp thành luật cho mọi refactor, vì no-op có thể đúng.

So sánh trạng thái cuối chứng minh trạng thái được giữ nguyên trong phạm vi đo. Nó không chứng minh chưa từng có ghi file rồi hoàn tác ở giữa phiên; tránh lời bảo đảm tuyệt đối đó.

### S-3: setup demo có thể cài skill ngoài project sẽ dùng

Báo cáo cài skill trước, sau đó tạo fixture trong `/tmp/...` và chuyển sang fixture. Với cài đặt project-scoped, thư mục cài ban đầu có thể không nằm trong phạm vi host tìm skill cho fixture.

Thứ tự dễ tái hiện hơn: tạo fixture → mở đúng project → cài skill trong project đó bằng biến thể đã kiểm tra → chuẩn bị baseline theo chính sách fixture → xác nhận host nhận đúng skill → chạy thử. Ghi riêng baseline của test có chủ đích thất bại, để người đọc không nhầm fixture lỗi với cài đặt lỗi.

Lệnh npx không pin phiên bản trong báo cáo không tự động sai, nhưng không nên thay thế command đã được thử trong docs bằng một phiên bản trôi nổi rồi giữ nguyên tuyên bố tested. “Try it in 30 seconds” nên đổi thành “Try a review-only task” trừ khi đã đo thời gian tương ứng.

### S-4: eight-page site là đề xuất, không phải ngưỡng SEO

Với một người duy trì hai skill, mình đề xuất khởi đầu bằng bốn trang: giới thiệu/chọn skill, cài đặt, một demo Refactor và một demo Foundation; liên kết tới evaluation hiện có. Tách guide riêng khi nội dung đã đủ sâu hoặc người đọc thực sự cần.

Báo cáo đặt cả hai proof assets đầu tiên vào Refactor và trì hoãn Foundation tới khi có tín hiệu nhu cầu. Điều đó dễ làm một nửa sản phẩm không có ví dụ để người mới đánh giá. Đưa một ví dụ Foundation nhỏ lên sớm hợp lý hơn việc viết thêm một guide chung.

Ước lượng 36–42 giờ nên được hiểu là ngân sách giả định. Không có dữ liệu năng suất của maintainer để biến nó thành cam kết; số trang và số link nội bộ không phải tiêu chí bảo đảm được index hoặc có click.

### S-5: kế hoạch Pages cần xử lý URL và nội dung hiện có

Các URL dạng `/installation/` và `/guides/.../` không tự được bảo đảm chỉ bằng việc tạo các file `.md` như cây thư mục trong báo cáo. Nếu dùng Jekyll, cần chọn permalink và baseurl phù hợp với project site, rồi kiểm tra HTML sinh ra. [Jekyll permalinks](https://jekyllrb.com/docs/permalinks/), [relative_url](https://jekyllrb.com/docs/liquid/filters/).

Repo đã có nhiều tài liệu review/kế hoạch trong `docs/`. Không nên mặc định xuất bản tất cả thành website. Chọn rõ tài liệu dành cho người dùng và loại báo cáo nội bộ khỏi site build; không tạo sitemap có các trang nháp hoặc hướng dẫn lỗi thời.

### S-6: đo lường đúng, nhưng sửa mẫu CSV

Hai điểm trong báo cáo được nguồn chính thức xác nhận:

- GitHub Traffic không đưa search engines và GitHub vào mục referring sites. [GitHub Traffic](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-traffic-to-a-repository).
- Bộ lọc branded queries của Google có điều kiện về property và lượng dữ liệu; không nên mặc định project-site URL sẽ có bộ lọc đó. [Google branded queries filter](https://developers.google.com/search/blog/2025/11/search-console-branded-filter).

Search Console cho website Pages không tự cung cấp dữ liệu truy vấn của trang repository nằm trên github.com. Tách dữ liệu theo property và ghi thời gian/cửa sổ đo rõ ràng.

Mẫu CSV trong báo cáo xuống dòng sau mỗi field, nên nếu lưu nguyên văn sẽ thành 16 dòng, không phải một header. Header dùng được:

```csv
week_start,repo_commit,pages_live,pages_indexed,search_impressions,search_clicks,search_ctr,top_nonbranded_query,top_landing_page,github_unique_visitors,github_unique_cloners,github_full_clones,skills_sh_listing_status,skills_sh_total_installs,external_issues,notes
```

Vẫn dùng N/A cho dữ liệu không có. Không cộng các cửa sổ 14 ngày chồng nhau thành tổng tháng, hoặc cộng unique visitors giữa tuần rồi coi là số người duy nhất trong tháng.

### S-7: câu chữ nên gọn và bớt khẩu hiệu

Các câu như “organic discovery engineering”, “manufacture usefulness” và “best documented and best evidenced answer” làm bản kế hoạch dài hơn nhưng không thêm tiêu chí thực thi. Không cần loại mọi câu có nhịp điệu; giữ một câu định vị, rồi dùng hành vi và bằng chứng cụ thể.

About đề xuất ngắn, chưa áp dụng lên GitHub:

```text
Agent skills for read-only code review, scoped refactoring, and repository development. Includes evaluation harnesses and archived comparison runs.
```

“Reproducible evaluation evidence” cần phân biệt chạy lại thí nghiệm với xác minh hash của archive. Harness/test chạy được không tự chứng minh người dùng tái tạo được kết quả model trong điều kiện lịch sử.

## Thứ tự làm tiếp theo mình đề xuất

1. Sửa backup reuse và Hidden manifest; thêm regression tests đúng hai lỗi đó.
2. Hoàn thiện nguồn trích dẫn và sửa phép kiểm tra no-mutation trong bản research trước khi chuyển thành hướng dẫn công khai.
3. Cập nhật About/topics/README khi chốt bản public; giữ câu chữ giới hạn theo bằng chứng.
4. Làm một demo Refactor và một demo Foundation, cùng hướng dẫn cài đã thử; không cần chờ đủ tám trang.
5. Xuất bản website nhỏ khi các trang có nội dung thật, kiểm tra URL, rồi mới thiết lập Search Console và ghi traffic.

Không có thao tác commit, push, đổi metadata, xuất bản Pages hay tạo lịch tự động nào trong lượt review này. Lựa chọn không quảng bá mạng xã hội trong tài liệu được xem là giả định của kế hoạch, không phải một lệnh thực thi mới.

## Bằng chứng cục bộ

```text
C:\Users\Natch\AppData\Local\Temp\skills-followup-suctkt2u
```

Thư mục chứa `guarded.ps1`, `results.json`, `acceptance-suite.log`, từng log probe, fixture và `seo-proof-probe.json`. Thông báo trong `reused-backup.log` được PowerShell ngắt dòng; phép nhận diện thông báo đã xử lý ngắt dòng đó. Kết luận dựa trên log cùng so sánh inventory/hash thực tế.
