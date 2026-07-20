(function (window, document) {
  if (typeof window.IntersectionObserver === "undefined") return;

  // 本页当前活动的观察者集合。每次（软）导航重建前，先全部断开——旧页的 heading
  // 节点已被 instant navigation 换掉，若不断开会持续观察已脱离文档的节点（内存泄漏），
  // 且会与新页观察者叠加导致 is-active 高亮错乱。
  let observers = [];

  function teardown() {
    for (const observer of observers) observer.disconnect();
    observers = [];
  }

  function register($toc) {
    const currentInView = new Set();
    const headingToMenu = new Map();
    const $menus = Array.from($toc.querySelectorAll('.md-nav__list > li > a'));

    for (const $menu of $menus) {
      // 修复既有 bug：TOC 链接的 href 可能是绝对 URL（取决于 site_url 配置），
      // getAttribute('href').slice(1) 会把 "http://..." 切成 "ttp://..."，永远匹配不到。
      // 改用 DOM .hash 属性：自动返回 "#fragment"，兼容相对/绝对两种 href。
      const rawHash = $menu.hash; // e.g. "#_2" or ""
      const elementId = rawHash ? rawHash.slice(1) : "";
      if (!elementId) continue;
      const $heading = document.getElementById(elementId);
      if ($heading) {
        headingToMenu.set($heading, $menu);
      }
    }

    const $headings = Array.from(headingToMenu.keys());

    const callback = (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          currentInView.add(entry.target);
        } else {
          currentInView.delete(entry.target);
        }
      }
      let $heading;
      if (currentInView.size) {
        // heading is the first in-view heading
        $heading = [...currentInView].sort(($el1, $el2) => $el1.offsetTop - $el2.offsetTop)[0];
      } else if ($headings.length) {
        // heading is the closest heading above the viewport top
        $heading = $headings
          .filter(($heading) => $heading.offsetTop < window.scrollY)
          .sort(($el1, $el2) => $el2.offsetTop - $el1.offsetTop)[0];
      }
      if ($heading && headingToMenu.has($heading)) {
        $menus.forEach(($menu) => $menu.classList.remove('is-active'));

        const $menu = headingToMenu.get($heading);
        $menu.classList.add('is-active');
        let $menuList = $menu.parentElement.parentElement.parentElement;
        while (
          $menuList.classList.contains('md-nav') &&
          $menuList.parentElement.tagName.toLowerCase() === 'li'
        ) {
          $menuList.parentElement.children[0].classList.add('is-active');
          $menuList = $menuList.parentElement.parentElement.parentElement;
        }
      }
    };
    const observer = new IntersectionObserver(callback, { threshold: 0 });
    observers.push(observer);

    for (const $heading of $headings) {
      observer.observe($heading);
      // smooth scroll to the heading
      if (headingToMenu.has($heading)) {
        const $menu = headingToMenu.get($heading);
        $menu.setAttribute('data-href', $menu.getAttribute('href'));
        $menu.setAttribute('href', 'javascript:;');
        $menu.addEventListener('click', () => {
          if (typeof $heading.scrollIntoView === 'function') {
            $heading.scrollIntoView({ behavior: 'smooth' });
          }
          const anchor = $menu.getAttribute('data-href');
          if (history.pushState) {
            history.pushState(null, null, anchor);
          } else {
            location.hash = anchor;
          }
        });
        $heading.style.scrollMargin = '4em';
      }
    }
  }

  // 每次文档就绪（含 instant navigation 软导航）：回收旧观察者，对当前页 TOC 重建。
  function setup() {
    teardown();
    document.querySelectorAll('.md-sidebar--secondary').forEach(register);
  }

  // window 级守卫：无论本脚本是否被软导航重放，document$ 订阅都只挂一次，避免累积订阅。
  if (window.document$ && typeof window.document$.subscribe === 'function') {
    if (!window.__tocSubscribed) {
      window.__tocSubscribed = true;
      window.document$.subscribe(setup);
    }
  } else if (document.readyState !== 'loading') {
    setup();
  } else {
    document.addEventListener('DOMContentLoaded', setup);
  }
})(window, document);
