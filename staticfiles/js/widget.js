var iNFTwidget = iNFTwidget || (function(){
    var _args = {}; // private
    var d = window,
        e = document,
        f = "text/javascript",
        g = "text/css",
        h = "stylesheet",
        k = "script",
        l = "link",
        m = "head",
        n = "complete",
        p = "UTF-8",
        q = ".";

    function r(b) {
        var a = e.getElementsByTagName(m)[0];
        a || (a = e.body.parentNode.appendChild(e.createElement(m)));
        a.appendChild(b)
    }

    function _loadJs(b) {
        var a = e.createElement(k);
        a.type = f;
        a.charset = p;
        a.src = b;
        r(a)
    }
    function _loadCss(b) {
        var a = e.createElement(l);
        a.type = g;
        a.rel = h;
        a.charset = p;
        a.href = b;
        r(a)
    }

    function $_GET(q,s) {
        s = s || window.location.search;
        var re = new RegExp('&'+q+'=([^&]*)','i');
        return (s=s.replace(/^\?/,'&').match(re)) ? s=s[1] : s='';
    }

    d.addEventListener && "undefined" == typeof e.readyState && d.addEventListener("DOMContentLoaded", function () {
        e.readyState = n
    }, !1);
    return {

        init : function(Args) {
            _args = Args;
            _loadJs(`https://backend-demo.alethea.ai/jobs/inft/?api_key=${_args[0]}&character=${_args[1]}`);
        },

    };
}());

