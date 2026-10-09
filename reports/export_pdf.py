"""Export the edited Markdown reports without rewriting their source files.

Install reportlab, then: python reports/export_pdf.py --output-dir reports/updated
Requires a TrueType font with Chinese glyphs; Windows YaHei is detected by default.
"""
from pathlib import Path
import argparse, html, re
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
import reportlab.lib.textsplit as textsplit
import reportlab.platypus.paragraph as paragraph_module

textsplit.ALL_CANNOT_START += '，；：！？'
paragraph_module.ALL_CANNOT_START = textsplit.ALL_CANNOT_START
COMMIT='d4b6071813a9c1353267d53dcfa9d8abc3e5b2f4'
PAGE_W, PAGE_H = A4
WIDTH = PAGE_W - 102

def fmt(text):
    output='';position=0
    for match in re.finditer(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',text):
        output += html.escape(text[position:match.start()]).replace(COMMIT,f'<font size="8.7">{COMMIT}</font>')
        output += f'<link href="{html.escape(match.group(2),quote=True)}" color="#214E75">{html.escape(match.group(1))}</link>'
        position=match.end()
    return output+html.escape(text[position:]).replace(COMMIT,f'<font size="8.7">{COMMIT}</font>')

def styles():
    body=ParagraphStyle('Body',fontName='CN',fontSize=10.4,leading=17.2,spaceAfter=8,rightIndent=6,textColor=colors.HexColor('#20252b'),wordWrap='CJK',allowWidows=0,allowOrphans=0)
    return {
        'body':body,
        'title':ParagraphStyle('Title',parent=body,fontName='CNBold',fontSize=19.5,leading=28,spaceAfter=18,textColor=colors.black),
        'heading':ParagraphStyle('Heading',parent=body,fontName='CNBold',fontSize=13.2,leading=21,spaceBefore=9,spaceAfter=9,textColor=colors.black,keepWithNext=True),
        'cell':ParagraphStyle('Cell',parent=body,fontSize=9,leading=14,spaceAfter=0),
        'small':ParagraphStyle('Small',parent=body,fontSize=8.7,leading=13,spaceAfter=8,textColor=colors.HexColor('#4b5563')),
    }

def table_block(lines,s):
    rows=[[v.strip() for v in line.strip().strip('|').split('|')] for line in lines if not re.match(r'^\|\s*:?-+',line)]
    count=len(rows[0]);assert all(len(r)==count for r in rows),'Malformed Markdown table'
    proportions={2:[.29,.71],3:[.30,.35,.35],4:[.25]*4,5:[.22,.27,.20,.155,.155]}.get(count,[1/count]*count)
    table=Table([[Paragraph(fmt(v),s['cell']) for v in row] for row in rows],colWidths=[WIDTH*v for v in proportions],repeatRows=1,hAlign='LEFT')
    commands=[('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7edf2')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#D9D9D9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]
    for index in range(2,len(rows),2):commands.append(('BACKGROUND',(0,index),(-1,index),colors.HexColor('#f7f9fb')))
    table.setStyle(TableStyle(commands))
    return [table,Spacer(1,12)]

def page_flow(md,s):
    result=[];lines=md.strip().splitlines();i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('|'):
            table_lines=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i]);i+=1
            result.extend(table_block(table_lines,s));continue
        if line.startswith('# '):result.append(Paragraph(fmt(line[2:]),s['title']))
        elif line.startswith('## '):result.append(Paragraph(fmt(line[3:]),s['heading']))
        else:
            parts=[line]
            while i+1<len(lines) and lines[i+1].strip() and not lines[i+1].startswith(('#','|')):
                i+=1;parts.append(lines[i].strip())
            value=' '.join(parts)
            result.append(Paragraph(fmt(value),s['small'] if value.startswith('实验依据：') else s['body']))
        i+=1
    return result

def footer(canvas,doc):
    canvas.saveState();canvas.setFont('CN',8);canvas.setFillColor(colors.HexColor('#67717b'))
    canvas.drawString(51,31,'Doodle Jump 强化学习课程项目   |   实验日期 2026年10月8日')
    canvas.drawRightString(PAGE_W-51,31,str(doc.page));canvas.restoreState()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file',type=Path,help='One Markdown report; otherwise export the five reports')
    parser.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent/'updated')
    parser.add_argument('--font',type=Path,default=Path('C:/Windows/Fonts/msyh.ttc'),help='Chinese TrueType font (.ttf or .ttc)')
    parser.add_argument('--bold-font',type=Path,default=Path('C:/Windows/Fonts/msyhbd.ttc'))
    parser.add_argument('--overwrite',action='store_true',help='Replace PDF files in the selected output directory')
    args=parser.parse_args()
    if not args.font.is_file():parser.error('Chinese font not found. Use --font /path/to/a/Chinese.ttf')
    bold=args.bold_font if args.bold_font.is_file() else args.font
    pdfmetrics.registerFont(TTFont('CN',str(args.font),subfontIndex=0))
    pdfmetrics.registerFont(TTFont('CNBold',str(bold),subfontIndex=0))
    inputs=[args.file.resolve()] if args.file else sorted(Path(__file__).resolve().parent.glob('*报告.md'))
    if not inputs:parser.error('No report Markdown files found')
    output=args.output_dir.resolve();output.mkdir(parents=True,exist_ok=True)
    targets=[output/(source.stem+'.pdf') for source in inputs]
    if not args.overwrite and any(target.exists() for target in targets):parser.error('PDF already exists; choose a new --output-dir or pass --overwrite')
    s=styles()
    for source,target in zip(inputs,targets):
        md=source.read_text(encoding='utf-8')
        story=[]
        for i,page in enumerate(re.split(r'<!--\s*pagebreak\s*-->',md)):
            if i:story.append(PageBreak())
            story.extend(page_flow(page,s))
        doc=SimpleDocTemplate(str(target),pagesize=A4,rightMargin=51,leftMargin=51,topMargin=45,bottomMargin=52,title=source.stem,author='Doodle Jump 强化学习课程项目',pageCompression=1)
        doc.build(story,onFirstPage=footer,onLaterPages=footer)
        print(target)

if __name__=='__main__':main()
