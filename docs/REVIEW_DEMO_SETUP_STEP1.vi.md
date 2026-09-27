# Review Bước 1: hoàn tất setup và bảo toàn lockfile

Ngày: 2026-09-27. Nhánh kiểm tra: `codex/demo-onboarding`. Phạm vi: thay đổi chưa commit của hai demo, module `examples/finalize_setup.py`, hướng dẫn và suite demo. Không phải đánh giá lại toàn bộ release hoặc hiệu quả hành vi của hai skill.

**Kết luận: chưa duyệt bản sửa hiện tại để chốt commit/push. Còn một lỗi P2 trong cam kết không ghi đè metadata.** Lỗi onboarding ban đầu đã được sửa và đã kiểm tra bằng CLI thật. Không cần thiết kế lại quy trình ba giai đoạn.

## 1. Kiểm tra trực tiếp

| Kiểm tra | Kết quả |
|---|---|
| `pwsh -NoProfile -File scripts/test-demos.ps1` | Exit 0; 40/40 PASS; native schema positive/negative controls PASS |
| `powershell.exe -NoProfile -File scripts/test-demos.ps1` | Exit 0; 40/40 PASS |
| Demo review: bootstrap mới → CLI 1.7.0 thật → finalize → verifier với báo cáo đối chứng | Exit 0; OVERALL VERIFICATION: PASSED |
| Demo foundation: bootstrap mới → CLI 1.7.0 thật → finalize → implementation đối chứng → verifier | Exit 0; OVERALL VERIFICATION: PASSED |
| Hai lượt finalize cùng fixture, được đồng bộ để cùng vượt kiểm tra tồn tại trước khi ghi | Cả hai SUCCESS: không đáp ứng yêu cầu chỉ tạo metadata một lần |
| `git diff --check` | Exit 0; có cảnh báo chuẩn hóa CRLF/LF, không có lỗi whitespace |
| Diff bootstrap, hai thư mục skill, archive lịch sử | Không có thay đổi ở các đường dẫn đó |

Lượt CLI thật dùng `--agent codex --copy -y`, tắt telemetry cho kiểm thử. Báo cáo review và implementation foundation là dữ liệu đối chứng để kiểm tra integration, không phải kết quả agent tự thực hiện nhiệm vụ.

Log integration lưu tại `C:/Users/Natch/AppData/Local/Temp/step1-review-qxgzf5ps/`, gồm hai file `*-install.log` và hai file `*-verify.log`.

## 2. [P2] Check-then-write không bảo đảm không ghi đè metadata

Vị trí: `examples/finalize_setup.py:115` và `:143`.

Hiện tại code kiểm tra `metadata_path.exists()`, thực hiện kiểm tra source rồi dùng `metadata_path.write_text(...)`. Thao tác cuối mở file theo chế độ ghi có thể cắt bỏ nội dung cũ. Kiểm tra tồn tại trước đó không khóa quyền tạo file.

Trường hợp lỗi: người dùng hoặc hai tiến trình chạy finalizer trên cùng fixture gần như đồng thời. Cả hai thấy metadata chưa tồn tại; sau đó cả hai ghi cùng đường dẫn và đều báo thành công. Lượt sau không nhận `FileExistsError`, trái với hợp đồng không chốt lại setup âm thầm.

Phép thử sử dụng implementation thật, chỉ chèn barrier sau khi `validate_pristine_source` chạy xong để tái hiện lịch xen kẽ ổn định:

```python
original = setup.validate_pristine_source
barrier = threading.Barrier(2)

def synchronized_validation(fixture):
    original(fixture)
    barrier.wait(timeout=15)

setup.validate_pristine_source = synchronized_validation
# Gọi setup.finalize_setup(fixture) từ hai worker trên cùng fixture mới.
# Quan sát hiện tại: cả hai trả về thành công, cùng một metadata_path.
```

Barrier không bỏ qua kiểm tra source và không thay thao tác ghi. Nó chỉ giữ hai lượt gọi ở vị trí có thể xảy ra khi thực thi đồng thời. Test chạy lại tuần tự hiện tại không bao phủ trường hợp này.

### Sửa tối thiểu

Dùng thao tác tạo file độc quyền tại thời điểm ghi, ví dụ:

```python
with metadata_path.open("x", encoding="utf-8") as stream:
    stream.write(json.dumps(metadata, indent=2) + "\n")
```

Giữ thông báo dễ hiểu khi gặp `FileExistsError`; kiểm tra tồn tại phía trước có thể giữ để báo lỗi sớm nhưng không được là cơ chế bảo vệ duy nhất. Không cần thêm thư viện hoặc xây hệ thống khóa phức tạp.

Nếu ghi thất bại giữa chừng và để lại file dở, các lượt sau phải từ chối hoặc báo metadata hỏng; không tự ghi đè để tiếp tục. Phạm vi bản sửa này không yêu cầu tuyên bố crash durability hoặc chống một tiến trình có toàn quyền sửa metadata bên ngoài fixture.

### Kiểm tra hồi quy cần thêm

- Hai lượt finalize cùng fixture qua một lịch xen kẽ được kiểm soát: đúng một lượt thành công, lượt còn lại nhận lỗi đã tồn tại.
- File kết quả là JSON hợp lệ của lượt thắng; lượt thua không cắt hoặc ghi đè nó.
- Test finalize lặp lại tuần tự và các test setup/lockfile hiện tại tiếp tục PASS.

## 3. Các chỉnh sửa nhỏ nên làm cùng đợt, không phải blocker độc lập

### Gọi đúng tên test mô phỏng CLI

`scripts/test_demos.py:796` trở đi đặt tên `...cli_install...`, nhưng các test đó gọi `_create_sample_lockfile()` và viết SKILL.md mẫu, không chạy npx.

Giữ test offline như hiện tại là hợp lý. Đổi tên/comment thành simulated CLI setup hoặc lockfile setup; ghi riêng lượt integration CLI thật. Không cần biến toàn bộ suite thành test phụ thuộc mạng.

### Đồng bộ số lượng test

`README.md:147`, `README.md:191` và comment `scripts/test-demos.ps1:84` vẫn ghi 23 trong khi suite hiện có 40. Sau khi bổ sung test mới, cập nhật số thực tế hoặc bỏ số hardcode khỏi chỗ không cần thiết. Đây là cập nhật dữ kiện của thay đổi kỹ thuật, không phải mở rộng công việc SEO.

### Diễn đạt phạm vi lockfile chính xác

Miễn trừ mới chỉ áp dụng cho đúng root `skills-lock.json`. Tuy nhiên ở Foundation, file bên trong vùng được phép sửa như `src/metric_hub/` vẫn tuân theo quy tắc scope hiện có. Không nên mô tả rằng mọi file có tên `skills-lock.json` trong tất cả thư mục con đều bị chặn; quy tắc thực tế là chúng không nhận miễn trừ đặc biệt và được kiểm tra theo scope bình thường.

## 4. Điều kiện để duyệt lại

1. Sửa thao tác tạo metadata thành exclusive creation và thêm test đồng thời.
2. Chạy lại suite demo trên hai PowerShell. Số test tăng bao nhiêu ghi theo output thực tế.
3. Đồng bộ các tên test/comment và số liệu cũ nêu trên.

Không cần thay bootstrap, baseline, INITIAL_HEAD, archive hoặc bổ sung quy tắc mới cho hai skill để giải quyết finding này. Sau bản sửa, review tiếp nên tập trung vào diff và các kiểm tra bị ảnh hưởng; không cần mở lại toàn bộ audit cũ.

Chưa stage, commit hoặc push. Lượt review này chỉ thêm tài liệu review này; mã triển khai của tác giả được giữ nguyên.
