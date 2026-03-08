import os

filepath = r"C:\Users\jhxox\Desktop\blolg_aoto\main_bot.py"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'ai_time_from_json_sa = obj.get("optimal_publish_time", "").strip()' in line:
        indent = line[:len(line) - len(line.lstrip())]
        inject = (
            f"{indent}ai_seo_tags_sa = obj.get('seo_tags', [])\n"
            f"{indent}final_tags_sa = list(set(tags_sa + ai_seo_tags_sa))\n"
            f"{indent}if len(final_tags_sa) > 30:\n"
            f"{indent}    final_tags_sa = final_tags_sa[:30]\n"
        )
        lines.insert(i + 1, inject)
        break

for i, line in enumerate(lines):
    if "naver.write_post(driver, title_sa, post_items_sa, tags=tags_sa," in line:
        lines[i] = line.replace("tags=tags_sa,", "tags=final_tags_sa,")
        break

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Track 2 tag merging patched in main_bot.py")
