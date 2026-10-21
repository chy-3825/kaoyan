#!/usr/bin/env python3
"""Assign one of the app's five exam-topic labels to every question.
2010-2022 use the four-module order used in those original exam papers;
2023-2026 have explicit row-level topic assignments because the topic order shifts.
Supplement questions inherit the exam-topic source collection they came from.
"""
from __future__ import annotations
import json, pathlib, collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
BANK=ROOT/'data/questions.jsonl'
LABELS={
 '马哲':'马克思主义基本原理',
 '思修':'思想道德与法治',
 '毛概':'毛泽东思想和中国特色社会主义理论体系概论',
 '史纲':'中国近现代史纲要',
 '习概':'习近平新时代中国特色社会主义思想概论',
}
VALID=tuple(LABELS.values())
TOPIC_OVERRIDES={
 'K政治-2009-05':'马克思主义基本原理', # circulation of money / political economy
 'K政治-2009-07':'马克思主义基本原理', # capital composition / political economy
 'K政治-2009-22':'马克思主义基本原理', # value of labor power / political economy
 'K政治-2009-25':'中国近现代史纲要', # founding of the Communist Party
 'K政治-2009-26':'毛泽东思想和中国特色社会主义理论体系概论', # new-democratic cultural program
}

# Row-level topic reading for recent papers; these papers mix topics within a
# year, so use each item's actual question content instead of its year/position.
RECENT={
2023:('史纲','马哲','马哲','马哲','毛概','习概','习概','习概','史纲','史纲','史纲','史纲','思修','习概','思修','习概','马哲','马哲','马哲','马哲','马哲','毛概','习概','习概','习概','习概','史纲','史纲','史纲','思修','思修','习概','习概'),
2024:('习概','马哲','习概','马哲','毛概','习概','习概','习概','史纲','史纲','史纲','史纲','史纲','习概','习概','习概','思修','习概','马哲','马哲','马哲','毛概','习概','习概','习概','习概','史纲','毛概','习概','思修','思修','习概','习概'),
2025:('习概','马哲','马哲','马哲','毛概','毛概','习概','习概','习概','史纲','史纲','史纲','史纲','思修','习概','习概','马哲','马哲','马哲','马哲','马哲','习概','习概','习概','习概','习概','史纲','史纲','毛概','思修','思修','习概','习概'),
2026:('马哲','马哲','马哲','马哲','毛概','毛概','习概','习概','习概','史纲','史纲','史纲','毛概','思修','史纲','习概','马哲','马哲','马哲','马哲','马哲','毛概','习概','习概','习概','习概','史纲','史纲','习概','思修','思修','习概','习概'),
}

HISTORY=(
'鸦片战争','南京条约','辛丑条约','甲午战争','洋务运动','戊戌变法','维新变法','义和团运动','辛亥革命','武昌起义','兴中会','同盟会','五四运动','一二·九运动','一二九运动','新文化运动','新民主主义革命','八七会议','南昌起义','秋收起义','广州起义','遵义会议','长征','抗日战争','卢沟桥事变','西安事变','百团大战','平型关大捷','重庆谈判','辽沈战役','淮海战役','平津战役','渡江战役','七七事变','九一八事变','西安事变','开国大典','抗美援朝','土地改革','第一届全国人民代表大会','第一届全国人民代表大会','社会主义革命和建设时期','十一届三中全会','十一届六中全会','中共一大','中国共产党第一次全国代表大会','中共二大','中共七大','中共六届六中全会','六届六中全会','中共八大','八七会议','新中国成立','中华人民共和国成立','台湾光复','光复台湾','新民主主义革命时期','新民主主义革命的胜利','清政府','半殖民地','半封建','近代中国','近代以来','帝国主义侵略','民族危机','民族独立和人民解放','资产阶级革命派','改良派','实业救国','护国运动','护法运动','北伐战争','抗日民族统一战线','第一次国共合作','第二次国共合作','工农武装割据','土地革命战争时期','文化大革命','改革开放和社会主义现代化建设新时期','抗日战争胜利','全面抗战','中国人民抗日战争','社会主义改造基本完成','政治协商会议','政协会议','重庆谈判','七届二中全会','西柏坡','港澳回归','香港回归','香港特别行政区成立','抗日战争胜利纪念日','南京大屠杀','戊戌维新运动','中国人民政治协商会议')
MAO_STRONG=(
'毛泽东思想','毛泽东思想活的灵魂','毛泽东思想是','中国特色社会主义理论体系','邓小平理论','“三个代表”重要思想','科学发展观','独立自主思想','人民内部矛盾','新民主主义理论','新民主主义社会','过渡时期总路线','人民民主专政','农村包围城市','武装夺取政权','一个中心、两个基本点','社会主义初级阶段','社会主义市场经济体制','一国两制','港人治港','工业化道路','毛泽东的思想路线')
MAO=(
'毛泽东思想','毛泽东同志','毛泽东在','毛泽东指出','毛泽东提出','毛泽东认为','毛泽东强调','《毛泽东选集》','《新民主主义论》','《论持久战》','《矛盾论》','《实践论》','《反对本本主义》','《中国革命和中国共产党》','《关于正确处理人民内部矛盾的问题》','延安整风','独立自主是毛泽东','邓小平理论','中国特色社会主义理论体系','科学发展观','“三个代表”重要思想','“三个代表”','社会主义初级阶段','社会主义市场经济体制','社会主义市场经济','改革开放的总设计师','南方谈话','南方讲话','社会主义改造','过渡时期总路线','人民民主专政','群众路线','实事求是','党的思想路线','新民主主义理论','新民主主义社会','农村包围城市','武装夺取政权','人民内部矛盾','人民民主统一战线','初级阶段基本路线','一个中心、两个基本点','邓小平理论的精髓','工业化道路','中国工业化道路','一国两制','港人治港','高度自治')
XI=(
'习近平新时代中国特色社会主义思想','习近平新时代思想','习近平法治思想','中国式现代化','新时代','新质生产力','新发展理念','高质量发展','两个结合','“两个结合”','第二个结合','两个确立','“两个确立”','两个维护','全过程人民民主','共同富裕','现代化强国','全面建设社会主义现代化国家','全面深化改革','全面依法治国','国家治理体系和治理能力','总体国家安全观','乡村振兴','粮食安全','绿水青山','生态文明建设','碳达峰','碳中和','人类命运共同体','一带一路','全球发展倡议','全球安全倡议','全球文明倡议','中国特色大国外交','新型国际关系','新时代党的建设','党的自我革命','全面从严治党','党的二十大','党的十八大以来','二十届中央','中央政治局','党中央','十四五','十五五','新时代中国特色社会主义','文化自信','文化主体性','中华文明','中华优秀传统文化','中华民族共同体','区域协调发展','创新驱动发展','有效市场和有为政府','民营经济','三农','扩大开放','改革开放只有进行时','政治安全','国家安全观','法治固根本','建设教育强国','科技强国','人才强国','中国外交','中国方案','中国智慧','外交关系','中非合作','金砖','国际关系','单边强制措施','外交','台湾问题与新时代中国统一事业','新发展格局','能源安全','民生','绿色发展','社会主要矛盾','党的领导是中国特色社会主义','党的领导是中国特色社会主义最本质','党的领导是中国特色社会主义制度的最大优势','以人民为中心','人民立场','人民至上','统一战线是党克敌制胜','枫桥经验','全国两会','中国共产党领导是中国特色社会主义最本质')
ETHICS=(
'理想信念','人生观','人生价值','价值观','道德','爱国主义','社会主义核心价值观','核心价值观','法律权利','法律义务','权利与义务','法律至上','法律思维','法治思维','依法行使权利','依法履行义务','宪法','民法典','刑法','隐私权','个人信息','诚信','集体主义','职业道德','社会公德','家庭美德','公民道德','道德建设','道德观','中国精神','民族精神','时代精神','爱国精神','劳动精神','奋斗精神','志愿服务','人生价值','择业观','就业观','恋爱观','婚姻家庭','公共生活','思想道德','思想政治教育','中华传统美德','传统美德','恋爱中的道德','法律责任','依法治国和以德治国','社会主义法治','正当防卫','网络安全法','消费者权益保护','个人信息保护','爱国主义教育法','法律面前人人平等','爱国主义教育法')
MARX=(
'马克思主义哲学','唯物辩证法','唯物史观','唯物论','辩证法','认识论','实践和认识','实践是检验真理','真理和价值','真理观','价值规律','剩余价值','劳动力商品','劳动价值论','商品价值','商品二因素','使用价值和价值','资本有机构成','资本积累','资本主义','垄断资本','平均利润','生产力与生产关系','生产力和生产关系','经济基础与上层建筑','社会存在和社会意识','人民群众是历史','人民群众创造历史','人的本质','社会形态','人类社会历史','社会基本矛盾','矛盾的普遍性','矛盾的特殊性','对立统一规律','质量互变规律','否定之否定','量变和质变','意识能动作用','主观能动性','物质和意识','联系和发展','联系、发展','偶然性与必然性','现象与本质','抽象与具体','价值的主体性','经济全球化','共产主义社会','科学社会主义','马克思、恩格斯','马克思指出','马克思认为','马克思主义','恩格斯','列宁指出','列宁认为','列宁在','商品经济','商品生产','私有制基础','剩余产品','土地所有制','利润率','劳动二重性','劳动过程','货币的本质','货币职能','社会再生产','金融资本','地理环境和人口因素','社会意识','人的认识','认识世界','认识过程','真理的客观性','生产方式')

def module_fallback(q):
 n=q['questionNo']
 if not n:return '马哲'
 if n<=4 or 17<=n<=21:return '马哲'
 if 5<=n<=8 or 22<=n<=25:return '毛概'
 if 9<=n<=12 or 26<=n<=29:return '史纲'
 return '思修'

def infer(q):
 if q['sourceType']=='supplement':
  existing=q.get('topicTag','')
  if existing in VALID:return existing,'reviewed source-topic assignment'
  topic=q.get('sourceTopic','')
  if '道德' in topic or '思修' in topic:return '思修','supplement collection'
  if '近现代史' in topic:return '史纲','supplement collection'
  if '毛泽东思想' in topic:return '毛概','supplement collection'
  return '马哲','supplement collection'
 year=q.get('examYear');n=q.get('questionNo')
 if year in RECENT and n and 1<=n<=33:return RECENT[year][n-1],f'{year} question-specific topic review'
 t=' '.join([q.get('stem',''),q.get('explanation','')])
 if any(k in t for k in MAO_STRONG):return '毛概','specific Mao and socialist-theory concept'
 if any(k in t for k in HISTORY):return '史纲','historical events and periods'
 if any(k in t for k in ETHICS):return '思修','ideological, ethical and legal studies'
 if any(k in t for k in MAO):return '毛概','Mao and socialist-theory curriculum'
 if any(k in t for k in XI):return '习概','Xi Jinping Thought and contemporary Chinese policy'
 if any(k in t for k in MARX):return '马哲','Marxist principles and political economy'
 return module_fallback(q),'original examination module order'

def tag_records(rows):
 counts=collections.Counter();rules=collections.Counter()
 for q in rows:
  if q.get('id') in TOPIC_OVERRIDES:tag,rule=TOPIC_OVERRIDES[q['id']],'reviewed topic correction'
  elif q.get('topicTag') in VALID:tag,rule=q['topicTag'],'preserved reviewed topic label'
  else:tag,rule=infer(q);tag=LABELS.get(tag,tag)
  if tag not in VALID:raise ValueError((q['id'],tag))
  q['topicTag']=tag;counts[tag]+=1;rules[rule]+=1
 return counts,rules

def write_outputs(rows):
 counts,_=tag_records(rows)
 BANK.write_text(''.join(json.dumps(q,ensure_ascii=False)+'\n' for q in rows),encoding='utf8')
 for out in [ROOT/'app/dist/questions.js',ROOT/'android/web/questions.js']:
  out.write_text('window.QUESTIONS='+json.dumps(rows,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
 ordered=dict((tag,counts[tag]) for tag in VALID)
 source_counts=collections.Counter(q.get('sourceName','') for q in rows if q['sourceType']=='supplement')
 review_counts=collections.Counter(q.get('explanationReviewStatus','source_provided' if q.get('explanationKind')!='generated' else 'answer_hint') for q in rows)
 by_course=collections.defaultdict(collections.Counter)
 for q in rows:by_course[q['topicTag']][q.get('explanationReviewStatus','source_provided' if q.get('explanationKind')!='generated' else 'answer_hint')]+=1
 summary={'total':len(rows),'withPreanalysis':sum(bool(q.get('explanation','').strip()) for q in rows),'generatedPreanalysis':sum(q.get('explanationKind')=='generated' for q in rows),'generatedWithSpecificRationaleRule':review_counts['specific_rationale'],'generatedAnswerHintsNeedSubjectReview':review_counts['answer_hint'],'byTopicTag':ordered,'pastExam':sum(q['sourceType']=='past_exam' for q in rows),'supplement':sum(q['sourceType']=='supplement' for q in rows),'supplementSources':dict(source_counts)}
 (ROOT/'data/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 audit={'total':len(rows),'sourceProvidedExplanations':review_counts['source_provided'],'generatedWithSpecificRationaleRule':review_counts['specific_rationale'],'generatedAnswerHintsNeedSubjectReview':review_counts['answer_hint'],'byCourse':{tag:dict(c) for tag,c in sorted(by_course.items())},'note':'A matched rationale rule is a focused draft, not independent expert verification. Answer hints explicitly lack item-specific distractor analysis.'}
 (ROOT/'data/preanalysis_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 manifest=ROOT/'sources/manifest.json'
 if manifest.exists():
  m=json.loads(manifest.read_text(encoding='utf8'));m['topicTags']={'available':list(VALID),'counts':ordered,'assignment':'Supplement labels follow source collections; 2023-2026 use question-specific subject mapping; 2009-2022 use topic keywords and the source paper section as fallback for short or cross-topic questions.'};manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(ordered,ensure_ascii=False))

if __name__=='__main__':
 rows=[json.loads(x) for x in BANK.read_text(encoding='utf8').splitlines()]
 counts,rules=tag_records(rows)
 write_outputs(rows)
 print('Rules:',json.dumps(rules,ensure_ascii=False))
