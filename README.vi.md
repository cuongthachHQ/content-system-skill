<div align="center">

[English](README.md) · **Tiếng Việt**

# CuongThach Content Skills

**Ý - Viết - Sửa · Phễu nội dung Biết - Tin - Yêu · Thông điệp lõi**

Bộ 7 skill giúp AI agent dẫn bạn làm một bài theo Ý - Viết - Sửa, từ hồ sơ thương hiệu tới bản nháp đã sửa, mà không viết thay bạn. Dựng từ phương pháp làm nội dung của [Cường Thạch](https://cuongthach.com/vi/).

[![GitHub stars](https://img.shields.io/github/stars/cuongthachHQ/content-system-skill?style=social)](https://github.com/cuongthachHQ/content-system-skill/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/cuongthachHQ/content-system-skill?style=social)](https://github.com/cuongthachHQ/content-system-skill/network/members)
[![Last commit](https://img.shields.io/github/last-commit/cuongthachHQ/content-system-skill)](https://github.com/cuongthachHQ/content-system-skill/commits)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](LICENSE)

[Trang chủ](https://cuongthach.com/vi/) · [Tài liệu](https://cuongthach.com/docs/vi/) · [Hướng dẫn cài](https://cuongthach.com/docs/vi/content-system/agent-skills/) · [Blog](https://cuongthach.com/vi/blog/)

</div>

---

Mỗi skill là một thư mục hướng dẫn mà AI agent nạp khi việc của bạn cần đến. Bộ skill này đưa Quy trình Ý - Viết - Sửa vào agent:

- Điền hồ sơ thương hiệu cùng bạn
- Xếp bài vào bài Biết, Tin hay Yêu
- Soạn câu hỏi ghi âm
- Ép thông điệp lõi
- Dẫn bạn chốt dàn ý, viết và sửa

**Ý tưởng và câu chữ vẫn do bạn viết.**

## Cần chuẩn bị

- [Claude Code](https://code.claude.com/docs/en/overview) hoặc [Antigravity](https://antigravity.google/), mở ở thư mục dự án nơi bạn làm nội dung
- [Node.js](https://nodejs.org/en/download) bản LTS mới nhất. Lệnh cài chạy bằng `npx`, đi kèm Node.js, và cần **ít nhất bản 22.20**

## Cài vào agent

**1. Cài 7 skill.** Cách nhanh nhất là dán câu này vào agent, agent tự chạy lệnh cài:

```text
Cài tất cả skill ở https://github.com/cuongthachHQ/content-system-skill vào dự án này bằng lệnh npx skills add, chọn đúng agent bạn đang chạy và thêm -y, rồi liệt kê các skill đã cài.
```

Hoặc tự chạy lệnh trong terminal, ở thư mục dự án:

```bash
# Claude Code
npx skills add cuongthachHQ/content-system-skill --skill '*' -a claude-code -y

# Antigravity
npx skills add cuongthachHQ/content-system-skill --skill '*' -a antigravity -y
```

Thêm `-g` vào cuối lệnh để dùng bộ skill ở mọi dự án trên máy.

**2. Kiểm skill đã vào agent.**

- **Trong Claude Code**, gõ `/` và thấy đủ 7 tên, skill nằm ở `.claude/skills/`.
- **Trong Antigravity**, hỏi *"Bạn đang có những skill nào?"*, skill nằm ở `.agents/skills/`.

**3. Gõ `/cuongthach`.** Skill chính hỏi bạn đang có gì: một đề tài, một bản ghi âm, một dàn ý đã chốt hay một bản nháp. Bạn trả lời, rồi nó chạy skill của bước tiếp theo, **không tự viết bài**.

## Bộ skill gồm gì

| Skill | Việc nó làm |
|---|---|
| `cuongthach` | Skill chính: xem bài đang ở bước nào, giao bước tiếp theo cho đúng skill, không tự làm bước nào |
| `ct-profile-create` | Điền hồ sơ thương hiệu 10 mục cùng bạn, hỏi từng mục, ghi `Chưa có` cho mục còn thiếu |
| `ct-post-classify` | Xếp bài vào đúng một loại: bài Biết, bài Tin hay bài Yêu |
| `ct-record-plan` | Soạn bộ câu hỏi ba nhóm Là gì, Như thế nào, Tại sao để bạn tự trả lời khi ghi âm |
| `ct-message-create` | Ép ba câu trả lời về khách hàng, vấn đề và giải pháp thành một câu thông điệp lõi |
| `ct-post-write` | Chạy ba bước Ý - Viết - Sửa: chốt dàn ý, viết bản nháp một mạch, rồi chỉ cắt |
| `cuongthach-update` | Xem có bản mới của bộ skill không, tóm tắt thay đổi, rồi cập nhật khi bạn đồng ý |

## Ví dụ cách dùng Skill

Một bài đi qua các skill theo thứ tự dưới đây. **Bạn chỉ cần gõ `/cuongthach`**, agent tự gọi bước tiếp theo, hoặc gõ thẳng tên skill khi đã biết mình ở bước nào.

- `/ct-profile-create`: điền hồ sơ thương hiệu 10 mục, làm một lần
- `/ct-post-classify Bài này là bài Biết, Tin hay Yêu?`: xếp loại bài trước khi viết
- `/ct-record-plan Bài Tin về cách viết từ ghi âm`: nhận bộ câu hỏi để tự ghi âm
- `/ct-message-create`: dán bản ghi âm, ép thành một câu thông điệp lõi
- `/ct-post-write`: lọc ý, chốt dàn ý, rồi viết và sửa

Bạn cũng có thể nói việc bằng lời thường, như *"Bài này tới bước nào rồi?"*, agent tự gọi skill có mô tả khớp.

## Cập nhật Skill

**Skill đổi theo docs**: khi một trang docs mà skill dựa vào thay đổi, bộ skill ra bản mới và ghi vào [CHANGELOG.md](CHANGELOG.md).

**Nên dùng `/cuongthach-update`.** Agent xem có bản mới không, tóm tắt thay đổi cho bạn đọc, rồi cập nhật khi bạn đồng ý. Không dùng agent thì chạy `npx skills update` trong thư mục dự án.

## Khi cài trục trặc

<details>
<summary>Lệnh npx báo lỗi</summary>

Thường do Node.js cũ hơn 22.20: **cài bản LTS mới nhất** rồi chạy lại. Vẫn lỗi thì cài tay: tải ZIP của repo này, chép từng thư mục trong `skills/` vào `.claude/skills/` cho Claude Code hoặc `.agents/skills/` cho Antigravity.
</details>

<details>
<summary>Agent không thấy skill</summary>

Agent đang mở ở thư mục khác chỗ đã cài. Mở agent đúng thư mục dự án, hoặc cài lại với `-g`.
</details>

<details>
<summary>Agent tự viết bài khi gõ /cuongthach</summary>

Skill chưa được nạp. Kiểm lại danh sách skill và chạy lại lệnh cài nếu thiếu tên nào.
</details>

## Roadmap

Các skill dự kiến, mỗi skill dựng từ một trang docs đã có. Bấm ⭐ và **Watch** để được báo khi skill mới ra.

| Skill dự kiến | Việc nó sẽ làm | Trang docs nguồn |
|---|---|---|
| `ct-post-edit` | Sửa bản nháp thô thành bài mà vẫn giữ nguyên dàn ý | [Sửa bản nháp](https://cuongthach.com/docs/vi/content-system/idea-write-edit/guides/tutorials/edit-a-draft/) |
| `ct-page-write` | Dựng trang bán hàng ngắn: tên, minh chứng, thanh toán | [Trang bán hàng ngắn](https://cuongthach.com/docs/vi/content-system/know-trust-love/guides/how-to/build-a-lean-sales-page/) |
| `ct-docs-write` | Bắt đầu Kho sự thật từ những gì bạn đã có | [Kho sự thật đầu tiên](https://cuongthach.com/docs/vi/content-system/truth-vault/guides/tutorials/build-the-first-vault/) |

## Nguồn

Mọi nội dung trong bộ skill được rút từ tài liệu công khai của Cường Thạch. Khi skill và tài liệu khác nhau, **tài liệu là bản đúng**:

- [Quy trình Ý - Viết - Sửa](https://cuongthach.com/docs/vi/content-system/idea-write-edit/introduction/)
- [Phễu nội dung Biết - Tin - Yêu](https://cuongthach.com/docs/vi/content-system/know-trust-love/introduction/)
- [Tạo thông điệp lõi](https://cuongthach.com/docs/vi/content-system/idea-write-edit/guides/how-to/create-a-core-message/)
- [AI và các câu lệnh mẫu](https://cuongthach.com/docs/vi/content-system/resources/ai-and-prompts/)
- [Mẫu hồ sơ thương hiệu](https://cuongthach.com/docs/vi/content-system/resources/brand-profile-template/)

## Bản quyền

© 2026 Cường Thạch ([cuongthach.com](https://cuongthach.com/)). Phát hành theo giấy phép [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

Bạn được dùng, sửa và chia sẻ lại, kể cả cho mục đích thương mại, miễn là **ghi nguồn** như sau:

```text
Dựa trên bộ skill CuongThach Content Skills của Cường Thạch (https://cuongthach.com/), giấy phép CC BY 4.0.
```

**Thuật ngữ thương hiệu:** "Hệ thống nội dung", "Phễu nội dung", "Biết - Tin - Yêu" và "Ý - Viết - Sửa", cùng tên tiếng Anh "Content system", "Know - Trust - Love" và "Idea - Write - Edit", là tên phương pháp của Cường Thạch. Khi nhắc lại, hãy giữ nguyên tên và ghi nguồn. Đừng dùng các tên này để ngụ ý sản phẩm của bạn được Cường Thạch bảo trợ.

## Ủng hộ

Nếu bộ skill giúp ích cho bạn, hãy bấm ⭐ ở đầu trang. Mỗi sao giúp người khác tìm thấy phương pháp này.

[![Star History Chart](https://api.star-history.com/svg?repos=cuongthachHQ/content-system-skill&type=Date)](https://star-history.com/#cuongthachHQ/content-system-skill&Date)
