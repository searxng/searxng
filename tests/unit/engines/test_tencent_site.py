# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

import json
from tests import SearxTestCase
from searx.engines import tencent


class TestTencentSiteSyntax(SearxTestCase):
    """Test Tencent engine dynamic site parameter support"""

    def test_site_syntax_at_end(self):
        """Test site: syntax at the end of query"""
        # Save original values
        original_api_key = tencent.api_key
        original_secret_key = tencent.secret_key
        original_site = tencent.site
        
        try:
            tencent.api_key = 'test_id'
            tencent.secret_key = 'test_key'
            tencent.site = ''
            
            params = tencent.request('Python教程 site:zhihu.com', {})
            
            # Check that site was extracted
            payload = json.loads(params['data'])
            self.assertEqual(payload['Site'], 'zhihu.com')
            # Check that query was cleaned
            self.assertEqual(payload['Query'], 'Python教程')
        finally:
            tencent.api_key = original_api_key
            tencent.secret_key = original_secret_key
            tencent.site = original_site

    def test_site_syntax_at_beginning(self):
        """Test site: syntax at the beginning of query"""
        original_api_key = tencent.api_key
        original_secret_key = tencent.secret_key
        original_site = tencent.site
        
        try:
            tencent.api_key = 'test_id'
            tencent.secret_key = 'test_key'
            tencent.site = ''
            
            params = tencent.request('site:github.com Python项目', {})
            
            payload = json.loads(params['data'])
            self.assertEqual(payload['Site'], 'github.com')
            self.assertEqual(payload['Query'], 'Python项目')
        finally:
            tencent.api_key = original_api_key
            tencent.secret_key = original_secret_key
            tencent.site = original_site

    def test_site_syntax_in_middle(self):
        """Test site: syntax in the middle of query"""
        original_api_key = tencent.api_key
        original_secret_key = tencent.secret_key
        original_site = tencent.site
        
        try:
            tencent.api_key = 'test_id'
            tencent.secret_key = 'test_key'
            tencent.site = ''
            
            params = tencent.request('Python site:csdn.net 教程', {})
            
            payload = json.loads(params['data'])
            self.assertEqual(payload['Site'], 'csdn.net')
            self.assertEqual(payload['Query'], 'Python  教程')
        finally:
            tencent.api_key = original_api_key
            tencent.secret_key = original_secret_key
            tencent.site = original_site

    def test_site_syntax_case_insensitive(self):
        """Test that site: syntax is case insensitive"""
        original_api_key = tencent.api_key
        original_secret_key = tencent.secret_key
        original_site = tencent.site
        
        try:
            tencent.api_key = 'test_id'
            tencent.secret_key = 'test_key'
            tencent.site = ''
            
            # Test uppercase SITE:
            params = tencent.request('Python SITE:GitHub.COM', {})
            payload = json.loads(params['data'])
            self.assertEqual(payload['Site'], 'GitHub.COM')
            self.assertEqual(payload['Query'], 'Python')
        finally:
            tencent.api_key = original_api_key
            tencent.secret_key = original_secret_key
            tencent.site = original_site

    def test_no_site_syntax(self):
        """Test query without site: syntax"""
        original_api_key = tencent.api_key
        original_secret_key = tencent.secret_key
        original_site = tencent.site
        
        try:
            tencent.api_key = 'test_id'
            tencent.secret_key = 'test_key'
            tencent.site = ''
            
            params = tencent.request('Python教程', {})
            
            payload = json.loads(params['data'])
            self.assertNotIn('Site', payload)
            self.assertEqual(payload['Query'], 'Python教程')
        finally:
            tencent.api_key = original_api_key
            tencent.secret_key = original_secret_key
            tencent.site = original_site

    def test_site_syntax_priority_over_static(self):
        """Test that dynamic site: syntax overrides static configuration"""
        original_api_key = tencent.api_key
        original_secret_key = tencent.secret_key
        original_site = tencent.site
        
        try:
            tencent.api_key = 'test_id'
            tencent.secret_key = 'test_key'
            tencent.site = 'zhihu.com'  # Static site
            
            # Dynamic site should override
            params = tencent.request('Python site:github.com', {})
            
            payload = json.loads(params['data'])
            self.assertEqual(payload['Site'], 'github.com')  # Dynamic wins
            self.assertEqual(payload['Query'], 'Python')
        finally:
            tencent.api_key = original_api_key
            tencent.secret_key = original_secret_key
            tencent.site = original_site

    def test_static_site_without_syntax(self):
        """Test that static site is used when no site: syntax in query"""
        original_api_key = tencent.api_key
        original_secret_key = tencent.secret_key
        original_site = tencent.site
        
        try:
            tencent.api_key = 'test_id'
            tencent.secret_key = 'test_key'
            tencent.site = 'zhihu.com'  # Static site
            
            params = tencent.request('Python教程', {})
            
            payload = json.loads(params['data'])
            self.assertEqual(payload['Site'], 'zhihu.com')  # Static site used
            self.assertEqual(payload['Query'], 'Python教程')
        finally:
            tencent.api_key = original_api_key
            tencent.secret_key = original_secret_key
            tencent.site = original_site

    def test_subdomain_site(self):
        """Test site: syntax with subdomain"""
        original_api_key = tencent.api_key
        original_secret_key = tencent.secret_key
        original_site = tencent.site
        
        try:
            tencent.api_key = 'test_id'
            tencent.secret_key = 'test_key'
            tencent.site = ''
            
            params = tencent.request('教程 site:blog.csdn.net', {})
            
            payload = json.loads(params['data'])
            self.assertEqual(payload['Site'], 'blog.csdn.net')
            self.assertEqual(payload['Query'], '教程')
        finally:
            tencent.api_key = original_api_key
            tencent.secret_key = original_secret_key
            tencent.site = original_site

    def test_multiple_site_syntax(self):
        """Test query with multiple site: (should use first match)"""
        original_api_key = tencent.api_key
        original_secret_key = tencent.secret_key
        original_site = tencent.site
        
        try:
            tencent.api_key = 'test_id'
            tencent.secret_key = 'test_key'
            tencent.site = ''
            
            # Multiple site: should use first one
            params = tencent.request('Python site:github.com site:zhihu.com', {})
            
            payload = json.loads(params['data'])
            self.assertEqual(payload['Site'], 'github.com')  # First match
        finally:
            tencent.api_key = original_api_key
            tencent.secret_key = original_secret_key
            tencent.site = original_site

