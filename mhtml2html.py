#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-10-09 12:13:05
# @Author  : Yangbin

import os
import re
import base64
import quopri
import email

re_str = r'<img.*?src="([^"<>]*?)".*?>' # [^"] 反选除'"'以外的字符, '?'表示非贪婪模式
img_p = re.compile(re_str)

def is_mhtml(doc_path):
    m = email.message_from_file(open(doc_path, "rb"))
    return m.is_multipart()

def mhtml2html(doc_path, save_path):
    m = email.message_from_file(open(doc_path, "rb"))
    if m.get("MIME-Version") != "1.0":
        return False
    if m.get_content_type() not in ["multipart/related"]: # 暂时只适配related
        return False
    # 只适配由一个html和多个图片组成的内容，一般html为第一个
    html_payload = None
    image_payloads = []
    for part in m.get_payload():
        encoder = part.get("Content-Transfer-Encoding", None)
        if encoder not in ["base64", "quoted-printable"]:
            return False
        # 可能存在多个text/html，假定第一个为main
        if part.get_content_type() == "text/html" and not html_payload:
            html_payload = part
            if encoder == "base64":
                html = base64.b64decode(html_payload.get_payload())
            elif encoder == "quoted-printable":
                html = quopri.decodestring(html_payload.get_payload())
            try:
                html = html.decode(html_payload.get_charsets()[0])
            except:
                pass
        elif part.get_content_type().startswith("image/") or \
            os.path.splitext(part.get("Content-Location", ""))[1].lower() in [".png", ".jpg", ".gif", ".jpeg"]:
            image_payloads.append(part)
    if not html:
        return False
    img_locs = img_p.findall(html)
    for image in image_payloads:
        cid = image.get("Content-ID", None)
        if cid:
            cid = "cid:%s" % cid[1:-1]
            old_img_src = '%s' % cid
            new_img_src = 'data:%s;base64,%s' % (image.get_content_type(), image.get_payload())
            html = html.replace(old_img_src, new_img_src)
            continue
        location = image.get("Content-Location", None)
        if location:
            #　location可能为绝对路径，需要正确截取文件名
            loc = None
            for img_loc in img_locs:
                if img_loc in location:
                    loc = img_loc
                    break
            if loc:
                old_img_src = '%s' % loc
                new_img_src = 'data:%s;base64,%s' % (image.get_content_type(), image.get_payload())
                html = html.replace(old_img_src, new_img_src)
            continue
        
    # utf-8或gb2312编码
    try:
        charset = html_payload.get_charsets()[0] 
    except:
        charset = "utf-8"
    # 没有设置header utf-8
    if html.startswith("<html><body>"):
        html = html.replace("<html>", "<html><head><meta charset=\"%s\"></head>" % charset)
    with open(save_path, "wb") as f:
        try:
            html = html.encode(charset)
        except:
            pass
        f.write(html)
    return True


if __name__ == '__main__':
    import sys
    print is_mhtml(sys.argv[1])
    print mhtml2html(sys.argv[1], sys.argv[2])
