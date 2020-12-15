"""
Test custom static page creation upon course creation.
"""
from mock import Mock, patch

from django.test import TestCase
from django.test.utils import override_settings

from contentstore.views.course import (
    _create_custom_static_page,
    _create_custom_video_xblock,
    _update_custom_tab_content,
    CUSTOM_VIDEO_METADATA,
    get_lms_root_url,
)
from contentstore.views.helpers import _update_custom_tabs_order


class DummyTab(object):
    """
    Mimic required static course tab functionality.
    """

    def __init__(self, name):
        self.name = name

    def __call__(self, *args, **kwargs):
        return self

    def __getitem__(self, item):
        return getattr(self, item)


class CustomStaticPageUtilsTest(TestCase):
    """
    Test utilities related to creation of a custom static page.

    The page is created upon new course creation and is
    very specific to AMAT.
    """

    def setUp(self):
        super(CustomStaticPageUtilsTest, self).setUp()
        self.tab_content = '''
            <p>Gary's Welcome</p>
            <iframe
              data-locator="{!s}"
              src="{!s}"
              style="width: 900px; height: 610px; border: none; overflow: hidden; display: block; margin: auto;"
            >
            </iframe>        
        '''

    @override_settings(LMS_BASE="example.com")
    def test_get_lms_root_url(self):
        """
        Test LMS root getter utility.

        No trailing slash in the url,
        protocol (https or http) is defined depending on
        the request arg (secure or not, respectively).
        """
        request = Mock()
        request.is_secure = Mock()

        request.is_secure.return_value = True
        url = get_lms_root_url(request)
        self.assertEqual(url, "https://example.com")

        request.is_secure.reset_mock()

        request.is_secure.return_value = False
        url = get_lms_root_url(request)
        self.assertEqual(url, "http://example.com")

    @patch("contentstore.views.course.BlockUsageLocator")
    @patch("contentstore.views.course.create_xblock")
    @patch("contentstore.views.course.modulestore")
    @patch("contentstore.views.course._get_xblock")
    @patch("contentstore.views.course._save_xblock")
    def test_create_custom_video_xblock(
        self,
        save_xblock_mck,
        get_xblock_mck,
        modulestore_mck,
        create_xblock_mck,
        loc_mck,
    ):
        """
        Test the util of custom video xblock creation.

        This is pretty straightforward:
        need to check that utils are called
        with proper arguments.
        """
        kourse = Mock()
        kourse.id = Mock()

        request = Mock()
        request.user = Mock()
        request.user.id = Mock()

        video_static_page = Mock()
        video_static_page.location = Mock()

        loc_mck.return_value = "loc"
        create_xblock_mck.return_value = video_static_page
        modulestore_mck.return_value = Mock()
        modulestore_mck.publish = Mock()
        get_xblock_mck.return_value = "Some xblock"
        save_xblock_mck.return_value = None

        xblock = _create_custom_video_xblock(request=request, course=kourse)

        self.assertEqual(xblock, "Some xblock")

        create_xblock_mck.assert_called_once_with(
            parent_locator="loc",
            user=request.user,
            category="video",
            display_name="",
            is_video_tab=True,
        )
        modulestore_mck.publish.assert_called_once()
        save_xblock_mck.assert_called_once_with(
            request.user,
            "Some xblock",
            metadata=CUSTOM_VIDEO_METADATA,
        )

    @patch("contentstore.views.course.BlockUsageLocator")
    @patch("contentstore.views.course.create_xblock")
    @patch("contentstore.views.course._update_custom_tab_content")
    @patch("contentstore.views.course._create_custom_video_xblock")
    @patch("contentstore.views.course._get_xblock")
    @patch("contentstore.views.course._save_xblock")
    def test_create_custom_static_page(
        self,
        save_xblock_mck,
        get_xblock_mck,
        create_custom_video_xblock,
        update_custom_tab_content_mck,
        create_xblock_mck,
        loc_mck,
    ):
        """
        Test the util of custom static page creation.

        Check that utils are called with proper arguments
        (video and tab are created with proper content).

        Ensure video locators are linked to a static page
        (for video to be editable and removable from a static page).
        """
        kourse = Mock()
        kourse.id = Mock()

        request = Mock()
        request.user = Mock()
        request.user.id = Mock()
        request.is_secure = Mock()
        request.is_secure.return_value = True

        video_xblock = Mock()
        video_xblock.location = Mock()

        static_xblock = Mock()
        static_xblock.location = Mock()

        intro_static_page = Mock()
        intro_static_page.location = Mock()

        loc_mck.return_value = "loc"
        save_xblock_mck.return_value = None

        create_custom_video_xblock.return_value = video_xblock
        create_xblock_mck.return_value = intro_static_page
        get_xblock_mck.return_value = static_xblock

        update_custom_tab_content_mck.return_value = "Some content"

        _create_custom_static_page(request=request, course=kourse, tab_content=self.tab_content)

        create_xblock_mck.assert_called_once_with(
            parent_locator="loc",
            user=request.user,
            category='static_tab',
            display_name="Learning on appliedx",
            update_custom_tabs_order=False,
        )

        update_custom_tab_content_mck.assert_called_once()

        save_xblock_mck.assert_called_once_with(
            request.user,
            static_xblock,
            data="Some content",
        )

        self.assertEqual(static_xblock.video_locators, [str(video_xblock.location)])

    @override_settings(LMS_BASE="example.com")
    def test_update_custom_tab_content(self):
        """
        Test the util updating custom tab content.

        Ensure the content's placeholders (iframe data-locator and src)
        get replaced with proper values.
        """
        request = Mock()
        request.is_secure = Mock()
        request.is_secure.return_value = True

        content = _update_custom_tab_content(
            request=request,
            locator="loc",
            content=self.tab_content,
        )

        self.assertEqual(
            content,
            self.tab_content.format(
                "loc",
                "https://example.com/xblock/loc",
            )
        )

    def test_update_custom_tabs_order(self):
        """
        Test the util updating course tabs order.

        Reordering happens per custom AMAT rules
        (see doctring of the util under test).
        """
        kourse = Mock()
        kourse.tabs = Mock()
        custom_tab = DummyTab(name="Learning on appliedx")
        tab1 = DummyTab(name="Discussion")
        tab2 = DummyTab(name="Wiki")
        tab3 = DummyTab(name="Progress")
        tab4 = DummyTab(name="Yammer Discussion")
        tab5 = DummyTab(name="Empty")

        # Case #1: progress tab exists, a new tab is placed right after it, no remaining tabs
        tabs = [tab1, tab2, tab3]
        kourse.tabs = tabs
        _update_custom_tabs_order(course=kourse, static_tab=custom_tab)
        self.assertEqual(kourse.tabs, [tab1, tab2, tab3, custom_tab])

        # Case #2: progress does not exist
        tabs = [tab1, tab2, tab4, tab5]
        kourse.tabs = tabs
        _update_custom_tabs_order(course=kourse, static_tab=custom_tab)
        self.assertEqual(kourse.tabs, tabs)

        # Case #3: a tab with new tab's name already exists
        tabs = [tab1, tab2, tab3, custom_tab]
        kourse.tabs = tabs
        _update_custom_tabs_order(course=kourse, static_tab=custom_tab)
        self.assertEqual(kourse.tabs, tabs)

        # Case #4: empty list of tabs passed in
        tabs = []
        kourse.tabs = tabs
        _update_custom_tabs_order(course=kourse, static_tab=custom_tab)
        self.assertEqual(kourse.tabs, tabs)

        # Case #5: progress tab exists, new tab is placed right after it, remaining tabs follow
        tabs = [tab1, tab2, tab3, tab4, tab5]
        kourse.tabs = tabs
        _update_custom_tabs_order(course=kourse, static_tab=custom_tab)
        self.assertEqual(kourse.tabs, [tab1, tab2, tab3, custom_tab, tab4, tab5])
