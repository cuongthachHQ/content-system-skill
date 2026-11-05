# What the converter already handles

Read it when a word in the `.txt` looks wrong and you need to know whether `md-to-tts-txt.py` should have handled it (step 3 of `SKILL.md`). These need no flag and no `fix.tsv` line.

- Names written with spaced dashes (Biết - Tin - Yêu, Know - Trust - Love, cặp Biết - Tin) are read straight on, "Biết Tin Yêu", with no pause at the dashes (user rule 2026-10-22); no `fix.tsv` line is needed for them.
- A rate with a slash ("từ/phút", "bài/ngày") is read "từ mỗi phút" (English "per"); a number with thousands dots at the end of a sentence ("khoảng 3.500.") is read whole. Both were read wrong ("từ hay phút", "ba.năm trăm") before the script was fixed on 2026-10-22. When reading the `.txt`, still look for a stray dot inside a number and "hay" between two words that meant a rate.
- Code blocks are never read, and that is where posts keep their prompts (` ```text `), so prompts are never read either (user rule 2026-10-22). Write a prompt in a post only as a code block.
- Asides in round brackets ("phễu (Phễu nội dung BTY)") are never read (user rule 2026-10-21).
- Acronyms are spelled with English letter names (user rule 2026-10-22: SEO "Ét i âu", AI "Ây ai", SMTP "Ét em ti pi"); BTY is said in full, "Biết Tin Yêu"; H1 to H6 written in the text are "heading một" ("heading 1" in English). An acronym English speakers say as a word (RAM, DMARC, TIN) goes in `SAID`, a word written in capitals (LIVE LINK, POST) in `CAPS_WORDS` of `md-to-tts-txt.py`; Vietnamese words in capitals ("THỜI GIAN") are read as words on their own. "ai" and "Ai" (the Vietnamese "who") are never touched.
