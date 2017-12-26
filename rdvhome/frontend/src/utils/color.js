export function hsb_to_hsl(h, s, v) {
    if (arguments.length === 1) {
        s = h.s, v = h.v, h = h.h;
    };

    var _h = h,
        _s = s * v,
        _l = (2 - s) * v;
    _s /= (_l <= 1) ? _l : 2 - _l;
    _l /= 2;

    return {
        h: _h,
        s: _s,
        l: _l
    };
}

export function hsl_to_hsb(h, s, l) {
    if (arguments.length === 1) {
        s = h.s, l = h.l, h = h.h;
    };
    
    var _h = h,
        _s,
        _v;

    l *= 2;
    s *= (l <= 1) ? l : 2 - l;
    _v = (l + s) / 2;
    _s = (2 * s) / (l + s);

    return {
        h: _h,
        s: _s,
        v: _v
    };
}

export function hsl_to_css(h, s, l) {
    if (arguments.length === 1) {
        s = h.s, l = h.l, h = h.h;
    }
    return 'hsl('+ Math.round(h*360) +', '+ Math.round(s*100) +'%, '+ Math.round(l*100)+'%)'  
}

export function hsb_to_css(h, s, b) {
    return hsl_to_css(hsb_to_hsl(h, s, b))
}