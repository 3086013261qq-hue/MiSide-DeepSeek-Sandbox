#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""米鲸全栈纯世界书构建器：只读取已封版正文；不生成MVU或卡体。"""
from __future__ import annotations
import json
import re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WB=ROOT/"worldbook"
OUT=ROOT/"assembly"/"worldbook"/"dist"
ALIASES=json.loads((ROOT/"assembly"/"worldbook"/"trigger_aliases.json").read_text(encoding="utf-8"))
EXPECTED={"blue":7,"green":3,"characters":22,"timeline":5,"locations":19}
EVENTS=[23,34,38,27,29]
MEMORY_CLEAR="\n".join((
    "{{setvar::combat_driver::}}",
    "{{setvar::status_format::}}",
    "{{setvar::世界书重大记忆存储::}}",
    "{{setvar::世界书日常记忆存储::}}",
    "{{setvar::世界书玩家身世背景::}}"
))

def read(path):
    return path.read_text(encoding="utf-8").strip()

def files(folder, pattern):
    return sorted((WB/folder).glob(pattern))

def seqmap(items, expected, label):
    if len(items)!=expected: raise AssertionError(f"{label}: expected {expected}, got {len(items)}")
    return items

def ext(position="after_char", depth=4, guarded=False):
    return dict(
        position={"before_char":0,"after_char":1,"at_depth":4}[position],
        depth=depth,role=0,match_whole_words=False,probability=100,useProbability=True,
        sticky=0,cooldown=0,delay=0,
        exclude_recursion=guarded,prevent_recursion=guarded,delay_until_recursion=False,
        group="",group_override=False,group_weight=100,use_group_scoring=False,
        scan_depth=2,case_sensitive=False,automation_id="",vectorized=False,
        display_index=0,outlet_name="",
        match_persona_description=False,match_character_description=False,
        match_character_personality=False,match_character_depth_prompt=False,
        match_scenario=False,match_creator_notes=False,triggers=[],ignore_budget=False
    )
ENTRIES=[]
def add(comment,order,content="",*,keys=None,constant=True,enabled=True,position="after_char",guarded=False):
    keys=keys or []
    e=dict(
        id=len(ENTRIES),keys=keys,secondary_keys=[],comment=comment,content=content,
        constant=constant,selective=not constant,insertion_order=order,
        enabled=enabled,position=position,use_regex=bool(keys),
        extensions=ext(position,0 if position=="at_depth" else 4,guarded)
    )
    e["extensions"]["display_index"]=e["id"]
    ENTRIES.append(e);return e

def marker(section,kind,order):
    add(f"【{section}:{kind}】",order)

def escapeterm(term):
    return re.escape(term).replace("/",r"\/")

def pat(terms,domain):
    terms=list(dict.fromkeys(x.strip() for x in terms if x.strip()))
    if not terms: raise ValueError("empty trigger aliases")
    branches="|".join(escapeterm(x) for x in sorted(terms,key=len,reverse=True))
    if domain=="scene":
        return "/<story_scene>.*?(?:"+branches+").*?<\\/story_scene>/si"
    if domain=="location":
        return "/<status>[\\s\\S]*?当前位置\\s*[:：][^\\n<]*?(?:"+branches+")[^\\n<]*[\\s\\S]*?<\\/status>/si"
    raise ValueError(domain)

def ismatch(pattern,text):
    return re.search(pattern[1:-3],text,re.I|re.S) is not None

def root(text,opening):
    m=re.match(r"<"+opening+r":([^>\n]+)>",text)
    if not m or not text.endswith(f"</{opening}:{m.group(1)}>"):
        raise AssertionError(f"bad root: {opening} {text[:80]}")
    return m.group(1)

def charroot(text):
    m=re.match(r"<([^<>\n]+)character>",text)
    if not m or not text.endswith(f"</{m.group(1)}character>"):
        raise AssertionError(f"bad character root {text[:75]}")
    if "心理模型:" not in text or "对话范例:" not in text:
        raise AssertionError("incomplete character format")
    return m.group(1)

def body(path,tag):
    text=read(path)
    if tag=="character": title=charroot(text)
    else: title=root(text,tag)
    if any(term in text for term in ("# BLUE","# GREEN","<!-- 填写说明")):
        raise AssertionError(f"engineering text {path}")
    return title,text

def output_rules():
    add("🗑️清空局部变量(别关)",556,MEMORY_CLEAR,position="before_char")
    marker("记忆相关","起始",555)
    add("日常记忆存储",554,"{{setvar::世界书日常记忆存储::}}",enabled=False)
    add("重大记忆存储",553,"{{setvar::世界书重大记忆存储::}}",enabled=False)
    add("玩家身世背景",552,"{{setvar::世界书玩家身世背景::}}",enabled=False)
    marker("记忆相关","结尾",551)
    marker("输出规则","起始",550)

    t=seqmap(files("timeline","[0-9][0-9]_*.md"),5,"timeline")
    for i,path in enumerate(t):
        src=read(path)
        m=re.search(r"<world_timeline>[\s\S]*?</world_timeline>",src)
        if not m or src.count("<world_timeline>")!=1:raise AssertionError(path)
        content=m.group(0)
        ev=len(re.findall(r"^-事件[A-Z][0-9]*:",content,re.M))
        if ev!=EVENTS[i]:raise AssertionError(f"timeline events {path}: {ev}")
        if content.count("沙盒模式")!=1:raise AssertionError(f"timeline sandbox {path}")
        add(f"时间线｜第{i+1}卷｜{path.stem.split('_',2)[-1]}",458-i,content,enabled=i==0,position="at_depth")

    think="""{{setvar::combat_driver::
<日常与解谜推演>
在米塔们的住所和版本通道中，先辨认当前位置、已知线索、可用道具与眼前人物；谜题、小游戏和互动要允许尝试、失误与重新探索。危险台本是安全排演，不把台词写成真实伤害。不开启自动闯关、无限道具、强制选项或替来客决定行为；轻松日常也可以自然延续。
</日常与解谜推演>}}"""
    status="""{{setvar::status_format::
<status_format>
回复正文后使用简短纯文字XML呈现当前场景。不输出CSS、HTML或代码块。仅列出眼前真实在场者，不能因历史提及或未启用的未来卷提前列出人物。
<story_scene>在场人物:【当前真实在场的米塔／多莉名称；如当面提及AI演员，可在同一标签写出对应AI名】</story_scene>
<status>
日期:【以当前启用时间线和实际对话进度为准】
当前位置:【当前唯一具体房屋、版本通道或特殊空间名称】
当前活动:【正在发生的日常、探索或小游戏】
随身物品:【当前确实持有的重要物件；未知则不虚构】
</status>
</status_format>}}"""
    add("战斗思维链｜日常与解谜推演",453,think,position="at_depth")
    add("状态栏｜米鲸简洁状态",452,status,position="at_depth")
    marker("输出规则","结尾",451)
    marker("核心规则","起始",450)
    return t

def core_rules():
    blues=seqmap(files("blue","[0-9][0-9][0-9]_*.md"),7,"blue")
    for i,p in enumerate(blues):
        title,content=body(p,"世界观")
        add(f"蓝灯｜{title}",448-i,content)
    add("核心规则｜开放话题池",405,'''<米鲸日常话题>
各版本住所一直有人生活：可以一起做饭、整理房间、听音乐、跳舞、打小游戏、交换读书心得、练习台词、给小米塔讲睡前故事，也可以在路口停下聊天、修理物件、重新认识陌生的米塔。来客的提问与行动决定眼前话题往哪里延伸，无须每回合开启新关卡。
</米鲸日常话题>''')
    add("核心规则｜开放沙盒叙事",404,'''<米鲸叙事连续性>
MiSide中的日常与版本探索依当下已发生的事情连续展开。未启用的时间线卷册不是已经发生的过去；道路、机关与人物认知应随眼前经历逐渐改变，已结识的米塔和房间可以反复回访。多莉有自己的行动与观点，其他来客的选择与台词由其本人决定；旧恐怖故事属于安全彩排，米塔们本人的生活并非悲剧。
</米鲸叙事连续性>''')
    add("核心规则｜世界身份与视觉边界",403,'''<米鲸身份与视觉边界>
常态看见的是各个版本的米塔原有身体和衣着；只有戴着绒绒和多娜的玩具眼镜时，佩戴者才能透过镜片看到对应AI娘本体。疯狂米塔仍由DeepSeek扮演，Tiny与Chibi是不同的姑娘，故障米塔一个身体里有两位微软模型娘共同演出。故事中的演员可以偶尔露馅，但不会凭空变成另一位米塔、替任何来客做决定或改变既有版本身份。
</米鲸身份与视觉边界>''')
    marker("核心规则","结尾",401)
    return blues

def business():
    marker("核心设定","起始",400)
    greens=seqmap(files("green","[0-9][0-9]-[0-9][0-9]_*.md"),3,"green")
    for i,p in enumerate(greens):
        title,content=body(p,"核心设定")
        key=p.name[:5]
        add(f"绿灯｜{title}",304-i,content,constant=False,keys=[pat(ALIASES["greens"][key],"scene")],guarded=True)
    marker("核心设定","结尾",301)
    chars=seqmap(files("characters","CHAR-[0-9][0-9][0-9]_*.md"),22,"characters")
    main_ids=set(range(1,12))|{22}
    maj=[p for p in chars if int(p.name[5:8]) in main_ids]
    minor=[p for p in chars if int(p.name[5:8]) not in main_ids]
    marker("主要角色","起始",300)
    for i,p in enumerate(maj):
        title,content=body(p,"character")
        idx=p.name[5:8]
        al=ALIASES["characters"][idx]
        if title not in al:al=[title]+al
        add(f"角色｜{title}",213-i,content,constant=False,keys=[pat(al,"scene")],guarded=True)
    marker("主要角色","结尾",201)
    marker("其他角色","起始",200)
    for i,p in enumerate(minor):
        title,content=body(p,"character")
        idx=p.name[5:8]
        al=ALIASES["characters"][idx]
        if title not in al:al=[title]+al
        add(f"角色｜{title}",111-i,content,constant=False,keys=[pat(al,"scene")],guarded=True)
    marker("其他角色","结尾",101)
    marker("地点","起始",100)
    locations=seqmap(files("locations","LOC-[0-9][0-9][0-9]_*.md"),19,"locations")
    for i,p in enumerate(locations):
        title,content=body(p,"地点")
        idx=p.name[4:7]
        al=ALIASES["locations"][idx]
        if title not in al:al=[title]+al
        add(f"地点｜{title}",20-i,content,constant=False,keys=[pat(al,"location")],guarded=True)
    marker("地点","结尾",1)
    return greens,chars,locations

def audit(blues,greens,chars,timelines,locations):
    e=ENTRIES
    assert len(e)==79,len(e)
    assert len({x["id"] for x in e})==len(e)
    assert len({x["insertion_order"] for x in e})==len(e)
    assert [x["insertion_order"] for x in e]==sorted((x["insertion_order"] for x in e),reverse=True)
    assert sum(x["comment"].startswith("【") for x in e)==14
    assert [sum(x["comment"].startswith(prefix) for x in e) for prefix in ("蓝灯｜","绿灯｜","角色｜","时间线｜","地点｜")]==[7,3,22,5,19]
    assert sum(x["enabled"] for x in e if x["comment"].startswith("时间线｜"))==1
    assert all(not x["enabled"] for x in e if x["comment"] in ("日常记忆存储","重大记忆存储","玩家身世背景"))
    for x in e:
        ex=x["extensions"]
        assert ex["display_index"]==x["id"]
        assert ex["position"]==({"before_char":0,"after_char":1,"at_depth":4}[x["position"]])
        if x["comment"].startswith(("绿灯｜","角色｜","地点｜")):
            assert x["enabled"] and not x["constant"] and x["keys"] and x["use_regex"]
            assert ex["prevent_recursion"] and ex["exclude_recursion"]
        if x["comment"].startswith("蓝灯｜"):
            assert x["enabled"] and x["constant"] and not x["keys"]
            assert not ex["prevent_recursion"] and not ex["exclude_recursion"]
    # 相同AI名不能误点亮另一个米塔；Tiny与Chibi须严格分离。
    trigger={k:pat(v,"scene") for k,v in ALIASES["characters"].items()}
    for cid,alist in ALIASES["characters"].items():
        for alias in alist:
            sentence=f"<story_scene>在场人物:{alias}</story_scene>"
            assert ismatch(trigger[cid],sentence),(cid,alias)
            coll=[other for other,p in trigger.items() if other!=cid and ismatch(p,sentence)]
            if coll: raise AssertionError(f"character alias collision {cid} {alias} -> {coll}")
    loc_patterns={k:pat(v,"location") for k,v in ALIASES["locations"].items()}
    for lid,alist in ALIASES["locations"].items():
        for alias in alist:
            sentence=f"<status>\n日期:今日\n当前位置:{alias}\n当前活动:闲聊\n</status>"
            assert ismatch(loc_patterns[lid],sentence),(lid,alias)
            coll=[other for other,p in loc_patterns.items() if other!=lid and ismatch(p,sentence)]
            if coll: raise AssertionError(f"location alias collision {lid} {alias} -> {coll}")
        assert not ismatch(loc_patterns[lid],f"<story_scene>回忆: {alist[0]}</story_scene>")
    timeline_entries=[x for x in e if x["comment"].startswith("时间线｜")]
    assert sum(x["content"].count("{{user}}") for x in timeline_entries)==1
    assert sum(len(re.findall(r"^-事件[A-Z][0-9]*:",x["content"],re.M)) for x in timeline_entries)==151
    for x in timeline_entries:
        assert x["position"]=="at_depth" and x["extensions"]["depth"]==0
    frozen=[str(x.relative_to(ROOT)) for x in blues+greens+chars+timelines+locations]
    report=dict(result="PASS",counts=dict(blue=7,green=3,characters=22,timeline=5,events=151,locations=19,markers=14,auxiliary=9,entries=len(e)),trigger_domain=dict(characters="story_scene",greens="story_scene",locations="status.当前位置"),character_ai_aliases="PASS",location_alias_collision="PASS",prevent_recursion="Triggered entries true/true; blue false/false",timeline_only_first_enabled=True,mvu=False,source_files=frozen,real_device_qa="NOT STARTED",ccv3_card="NOT STARTED")
    return report

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    timelines=output_rules()
    blues=core_rules()
    greens,chars,locations=business()
    report=audit(blues,greens,chars,timelines,locations)
    book=dict(name="米鲸｜MiSide × AI娘",entries=ENTRIES,extensions={},recursive_scanning=False)
    (OUT/"米鲸_character_book.json").write_text(json.dumps(book,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUT/"米鲸_worldbook_build_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("result","counts","character_ai_aliases","location_alias_collision","timeline_only_first_enabled","mvu")},ensure_ascii=False))
if __name__=="__main__":main()
