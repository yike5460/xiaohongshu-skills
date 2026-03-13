"""模拟人类浏览行为：通过搜索框搜索 → 分析页面结构 → 按顺序浏览笔记。

反风控设计：
- 不使用 URL 直接跳转，通过搜索框 UI 输入关键词
- 逐字键盘输入模拟真实打字
- 按从左到右、从上到下的自然阅读顺序浏览
- 先获取 DOM 结构再操作，避免盲目点击
- 所有操作带随机间隔
"""

from __future__ import annotations

import base64
import json
import logging
import random
import time
from pathlib import Path

from .cdp import Page
from .human import sleep_random, navigation_delay
from .urls import EXPLORE_URL

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = Path("/tmp/xhs/screenshots")

# ========== 选择器 ==========
SEARCH_INPUT = "input.search-input"
SEARCH_INPUT_ACTIVE = "#search-input"  # 搜索激活后的输入框

# 笔记卡片
FEED_CARD = "section.note-item"
FEED_CARD_COVER = "a.cover"

# 详情弹窗
DETAIL_NOTE_CONTAINER = "#noteContainer"
DETAIL_CLOSE = ".close-circle"


# ========== 搜索框交互 ==========


def _ensure_on_explore(page: Page) -> None:
    """确保当前在小红书首页。如果不在，导航过去。

    首页是正常的浏览器入口，允许直接导航。
    """
    current = page.evaluate("location.href") or ""
    if "xiaohongshu.com" not in current:
        logger.info("不在小红书，导航到首页")
        page.navigate(EXPLORE_URL)
        page.wait_for_load()
        navigation_delay()


def _search_via_ui(page: Page, keyword: str) -> None:
    """通过搜索框 UI 输入关键词并搜索（不使用 URL 跳转）。

    流程：
    1. 点击搜索框激活
    2. 逐字输入关键词（CDP 键盘事件）
    3. 按 Enter 提交搜索
    """
    _ensure_on_explore(page)
    sleep_random(500, 1000)

    # 点击搜索框
    logger.info("点击搜索框")
    page.click_element(SEARCH_INPUT)
    sleep_random(300, 600)

    # 等待搜索输入框激活
    time.sleep(0.5)

    # 清空可能存在的旧内容
    page._send_session("Input.dispatchKeyEvent", {
        "type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 2,
    })
    page._send_session("Input.dispatchKeyEvent", {
        "type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 2,
    })
    page._send_session("Input.dispatchKeyEvent", {
        "type": "keyDown", "key": "Backspace", "code": "Backspace",
        "windowsVirtualKeyCode": 8,
    })
    page._send_session("Input.dispatchKeyEvent", {
        "type": "keyUp", "key": "Backspace", "code": "Backspace",
        "windowsVirtualKeyCode": 8,
    })
    sleep_random(200, 400)

    # 逐字输入关键词
    logger.info("输入关键词: %s", keyword)
    for char in keyword:
        page._send_session("Input.dispatchKeyEvent", {
            "type": "keyDown", "text": char,
        })
        page._send_session("Input.dispatchKeyEvent", {
            "type": "keyUp", "text": char,
        })
        sleep_random(50, 120)

    sleep_random(300, 600)

    # 按 Enter 搜索
    logger.info("按 Enter 提交搜索")
    page._send_session("Input.dispatchKeyEvent", {
        "type": "keyDown", "key": "Enter", "code": "Enter",
        "windowsVirtualKeyCode": 13,
    })
    page._send_session("Input.dispatchKeyEvent", {
        "type": "keyUp", "key": "Enter", "code": "Enter",
        "windowsVirtualKeyCode": 13,
    })

    # 等待搜索结果加载
    page.wait_for_load()
    sleep_random(2000, 3500)
    page.wait_dom_stable()


# ========== 页面结构分析 ==========


def _analyze_feed_cards(page: Page) -> list[dict]:
    """分析当前页面的笔记卡片布局。

    返回按从左到右、从上到下排序的卡片列表，
    每个卡片包含位置、标题、索引等信息。
    """
    cards = page.evaluate("""
        (() => {
            const cards = document.querySelectorAll('section.note-item');
            return Array.from(cards).map((card, i) => {
                const rect = card.getBoundingClientRect();
                const link = card.querySelector('a.cover, a');
                const title = card.querySelector('.title span, .note-item .title');
                const author = card.querySelector('.author-wrapper .name, .author .name');
                const likes = card.querySelector('.like-wrapper .count, [class*="like"] .count');
                return {
                    index: i,
                    title: title?.innerText?.trim() || '',
                    author: author?.innerText?.trim() || '',
                    likes: likes?.innerText?.trim() || '',
                    href: link?.href || '',
                    top: Math.round(rect.top),
                    left: Math.round(rect.left),
                    bottom: Math.round(rect.bottom),
                    right: Math.round(rect.right),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    visible: rect.top < window.innerHeight && rect.bottom > 0,
                    centerX: Math.round(rect.left + rect.width / 2),
                    centerY: Math.round(rect.top + rect.height / 2),
                };
            });
        })()
    """)
    if not isinstance(cards, list):
        return []

    # 按行列排序：先按 top 分组（容差 50px），组内按 left 排序
    cards.sort(key=lambda c: (c["top"] // 50, c["left"]))
    logger.info("分析页面: 共 %d 张卡片", len(cards))
    return cards


# ========== 详情页交互与信息提取 ==========


def _extract_detail_info(page: Page) -> dict:
    """从笔记详情弹窗中提取完整信息。"""
    info = page.evaluate("""
        (() => {
            const container = document.querySelector('#noteContainer, .note-detail-mask');
            if (!container) return null;

            // 标题
            const title = container.querySelector('#detail-title, .title')?.innerText?.trim() || '';

            // 正文
            const desc = container.querySelector('#detail-desc, .desc, .note-text');
            const content = desc?.innerText?.trim() || '';

            // 作者
            const author = container.querySelector('.author-wrapper .username, .author-container .username, [class*=author] .name')?.innerText?.trim() || '';

            // 互动数据
            const likeEl = container.querySelector('.like-wrapper .count, [class*="like-active"] ~ .count, .engage-bar .like .count, .engage-bar-style .like .count');
            const collectEl = container.querySelector('.collect-wrapper .count, .engage-bar .collect .count, .engage-bar-style .collect .count');
            const commentEl = container.querySelector('.chat-wrapper .count, .engage-bar .chat .count, .engage-bar-style .chat .count');

            // 图片列表
            const images = container.querySelectorAll('.swiper-slide img, .carousel img, .note-image img');
            const imageUrls = Array.from(images).map(img => img.src).filter(Boolean);

            // 标签
            const tags = container.querySelectorAll('.tag a, .hash-tag a, #hash-tag a');
            const tagTexts = Array.from(tags).map(t => t.innerText?.trim()).filter(Boolean);

            // 评论（前几条）
            const comments = container.querySelectorAll('.parent-comment, .comment-item');
            const commentList = Array.from(comments).slice(0, 5).map(c => {
                const cAuthor = c.querySelector('.name, .author')?.innerText?.trim() || '';
                const cContent = c.querySelector('.content, .text')?.innerText?.trim() || '';
                const cLikes = c.querySelector('.like .count, [class*=like] .count')?.innerText?.trim() || '';
                return {author: cAuthor, content: cContent, likes: cLikes};
            });

            return {
                title: title,
                content: content,
                author: author,
                likes: likeEl?.innerText?.trim() || '',
                collects: collectEl?.innerText?.trim() || '',
                comments_count: commentEl?.innerText?.trim() || '',
                image_urls: imageUrls,
                tags: tagTexts,
                top_comments: commentList,
            };
        })()
    """)
    return info if isinstance(info, dict) else {}


def _take_screenshot(page: Page, name: str) -> str:
    """全屏截图，返回文件路径。"""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    result = page._send_session("Page.captureScreenshot", {"format": "png"})
    data = base64.b64decode(result.get("data", ""))
    path = SCREENSHOT_DIR / f"{name}.png"
    path.write_bytes(data)
    logger.info("截图: %s (%d bytes)", path, len(data))
    return str(path)


def _smooth_scroll(page: Page, distance: int) -> None:
    """模拟人类平滑滚动。"""
    steps = random.randint(3, 6)
    step_distance = distance / steps
    for _ in range(steps):
        page.dispatch_wheel_event(step_distance + random.uniform(-20, 20))
        time.sleep(random.uniform(0.05, 0.15))


def _click_card_by_position(page: Page, card: dict) -> bool:
    """通过位置点击笔记卡片（模拟鼠标行为）。"""
    if not card.get("visible"):
        # 先滚动到可见
        page.scroll_nth_element_into_view(FEED_CARD, card["index"])
        sleep_random(500, 1000)

    # 重新获取位置（滚动后可能变化）
    new_pos = page.evaluate(f"""
        (() => {{
            const cards = document.querySelectorAll('section.note-item');
            const card = cards[{card['index']}];
            if (!card) return null;
            const rect = card.getBoundingClientRect();
            return {{
                centerX: rect.left + rect.width / 2,
                centerY: rect.top + rect.height / 2,
                visible: rect.top < window.innerHeight && rect.bottom > 0,
            }};
        }})()
    """)
    if not new_pos or not new_pos.get("visible"):
        return False

    x = new_pos["centerX"] + random.uniform(-20, 20)
    y = new_pos["centerY"] + random.uniform(-20, 20)

    # 悬停
    page.mouse_move(x, y)
    sleep_random(500, 2000)

    # 点击
    page.mouse_click(x, y)
    sleep_random(1000, 2000)
    return True


def _close_detail(page: Page) -> None:
    """关闭详情弹窗。"""
    closed = page.evaluate("""
        (() => {
            const btn = document.querySelector('.close-circle, .note-detail-mask .close, [class*=close-btn]');
            if (btn) { btn.click(); return 'clicked'; }
            return 'not_found';
        })()
    """)
    if closed == "not_found":
        page._send_session("Input.dispatchKeyEvent", {
            "type": "keyDown", "key": "Escape", "code": "Escape",
            "windowsVirtualKeyCode": 27,
        })
        page._send_session("Input.dispatchKeyEvent", {
            "type": "keyUp", "key": "Escape", "code": "Escape",
            "windowsVirtualKeyCode": 27,
        })
    sleep_random(500, 1000)


# ========== 主入口 ==========


def browse_keyword(
    page: Page,
    keyword: str,
    max_notes: int = 10,
    max_time: float = 300.0,
    on_note: callable = None,
) -> list[dict]:
    """以人类节奏浏览关键词搜索结果。

    完整流程：
    1. 通过搜索框 UI 输入关键词搜索（不使用 URL 跳转）
    2. 分析页面 DOM 结构，获取卡片布局
    3. 按从左到右、从上到下的顺序逐个打开笔记
    4. 从详情弹窗提取完整信息（标题、正文、作者、互动数据等）
    5. 截取详情页截图
    6. 返回所有浏览结果

    Args:
        page: CDP 页面对象。
        keyword: 搜索关键词。
        max_notes: 最多浏览的笔记数量。
        max_time: 最大浏览时间（秒）。
        on_note: 每浏览一条笔记的回调 fn(index, info)。

    Returns:
        浏览过的笔记信息列表（含截图路径）。
    """
    start_time = time.monotonic()
    browsed_notes = []
    screenshots = []

    # 清理旧截图
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    for old in SCREENSHOT_DIR.glob("*.png"):
        old.unlink(missing_ok=True)

    # ===== 第一步：通过搜索框搜索 =====
    _search_via_ui(page, keyword)

    # 截图搜索结果页
    ss = _take_screenshot(page, "01_search_results")
    screenshots.append(ss)

    # ===== 第二步：分析页面结构 =====
    cards = _analyze_feed_cards(page)
    if not cards:
        logger.warning("未找到搜索结果卡片")
        return browsed_notes

    visible_cards = [c for c in cards if c.get("visible")]
    logger.info("可见卡片: %d/%d", len(visible_cards), len(cards))

    # ===== 第三步：按顺序浏览笔记 =====
    card_queue = list(cards)  # 已按从左到右、从上到下排序
    browsed_indices = set()
    screenshot_idx = 2

    for card in card_queue:
        # 检查限制
        if len(browsed_notes) >= max_notes:
            break
        elapsed = time.monotonic() - start_time
        if elapsed > max_time:
            logger.info("达到时间限制 %.0fs", elapsed)
            break
        if card["index"] in browsed_indices:
            continue

        browsed_indices.add(card["index"])

        # 如果卡片不可见，滚动使其可见
        if not card.get("visible"):
            _smooth_scroll(page, random.randint(300, 500))
            sleep_random(1000, 2000)
            # 刷新卡片列表获取新的可见卡片
            refreshed = _analyze_feed_cards(page)
            new_visible = [c for c in refreshed if c.get("visible") and c["index"] not in browsed_indices]
            if not new_visible:
                continue
            card = new_visible[0]
            browsed_indices.add(card["index"])

        # 点击卡片
        logger.info("打开笔记 #%d: %s", card["index"], card.get("title", "")[:30])
        if not _click_card_by_position(page, card):
            logger.warning("点击卡片失败: #%d", card["index"])
            continue

        # 等待详情弹窗加载
        sleep_random(1500, 2500)

        # 提取详情信息
        info = _extract_detail_info(page)
        if not info:
            info = {"title": card.get("title", ""), "author": card.get("author", "")}

        info["card_title"] = card.get("title", "")
        info["card_index"] = card["index"]

        # 模拟阅读（随机滚动详情页）
        scroll_times = random.randint(2, 5)
        for _ in range(scroll_times):
            _smooth_scroll(page, random.randint(150, 350))
            sleep_random(800, 2500)

        # 截图
        ss = _take_screenshot(page, f"{screenshot_idx:02d}_detail_{card['index']}")
        screenshots.append(ss)
        info["screenshot"] = ss
        screenshot_idx += 1

        browsed_notes.append(info)
        note_num = len(browsed_notes)
        logger.info(
            "已浏览 %d/%d: %s (by %s, 👍%s)",
            note_num, max_notes,
            info.get("title", "")[:30],
            info.get("author", "未知"),
            info.get("likes", "?"),
        )

        if on_note:
            on_note(note_num, info)

        # 关闭详情
        sleep_random(500, 1500)
        _close_detail(page)
        sleep_random(1000, 2500)

    # 最终截图
    ss = _take_screenshot(page, f"{screenshot_idx:02d}_final")
    screenshots.append(ss)

    elapsed = time.monotonic() - start_time
    logger.info("浏览完成: 共 %d 条笔记, 耗时 %.0f 秒, %d 张截图", len(browsed_notes), elapsed, len(screenshots))

    return browsed_notes
