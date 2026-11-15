#!/usr/bin/env python
# License: GPLv3 Copyright: 2026, maskshell fork
'''Stylesheet links are not BadDestinationType; Markdown TOC ids are short+valid.'''

from __future__ import annotations

import os
import re
import unittest

from calibre.ebooks.oeb.polish.check.links import BadDestinationType, check_links
from calibre.ebooks.oeb.polish.container import get_container
from calibre.ebooks.oeb.polish.tests.base import BaseTest
from calibre.ebooks.oeb.polish.tests.structure import cmi, create_epub
from calibre.ebooks.txt.processor import convert_markdown, short_valid_toc_slugify


class NavDestinationAndMdIdTests(BaseTest):
    def test_stylesheet_link_not_bad_destination_type(self) -> None:
        html = (
            '<html xmlns="http://www.w3.org/1999/xhtml"><head>'
            '<link rel="stylesheet" type="text/css" href="stylesheet.css"/>'
            '<link rel="stylesheet" type="text/css" href="page_styles.css"/>'
            '</head><body>'
            '<p><a href="stylesheet.css">bad nav to css</a></p>'
            '<p><a href="cover.jpeg">bad nav to image</a></p>'
            '<p>ok</p></body></html>'
        )
        ep = os.path.join(self.tdir, 'nav-dest.epub')
        with open(ep, 'wb') as f:
            f.write(
                create_epub(
                    [
                        cmi('index.html', html),
                        cmi('stylesheet.css', 'p { margin: 0 }'),
                        cmi('page_styles.css', '@page { margin: 0 }'),
                        cmi('cover.jpeg', b'\xff\xd8\xff\xd9'),
                    ]
                ).getvalue()
            )
        c = get_container(ep, tdir=os.path.join(self.tdir, 'nav-dest-c'), tweak_mode=True)
        errors = check_links(c)
        bad = [e for e in errors if isinstance(e, BadDestinationType)]
        hrefs = sorted(e.bad_href for e in bad)
        # Resource <link rel=stylesheet> must not warn; <a href> to non-HTML must.
        self.assertEqual(hrefs, ['cover.jpeg', 'stylesheet.css'])

    def test_short_valid_toc_slugify(self) -> None:
        self.assertEqual(short_valid_toc_slugify('第7章 被群灭的不良们', '-'), 'id7')
        self.assertEqual(short_valid_toc_slugify('第一卷', '-'), 'id')
        self.assertEqual(short_valid_toc_slugify('Chapter 7 Hello', '-'), 'chapter-7-hello')
        self.assertRegex(short_valid_toc_slugify('7', '-'), r'^[A-Za-z]')

    def test_markdown_chinese_headings_get_valid_short_ids(self) -> None:
        html = convert_markdown('## 第一卷\n\n### 第1章 黄山\n\npara\n\n### 第2章 测试\n\npara2\n')
        ids = re.findall(r'<h[23] id="([^"]+)"', html)
        self.assertEqual(len(ids), 3)
        for eid in ids:
            self.assertRegex(eid, r'^[A-Za-z][A-Za-z0-9_-]*$', msg=eid)
            self.assertLessEqual(len(eid), 24, msg=eid)
        # Distinct and short-ish
        self.assertEqual(len(set(ids)), 3)
        self.assertTrue(all(len(e) <= 8 for e in ids))


if __name__ == '__main__':
    unittest.main(verbosity=2)
