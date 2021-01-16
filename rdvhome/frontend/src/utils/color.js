import is_string     from 'rfuncs/functions/is_string'

export function hsb_to_hsl(data) {
    var s = data.saturation;
    var v = data.brightness;
    var h = data.hue;

    var _h = h,
        _s = s * v,
        _l = (2 - s) * v;
    _s /= (_l <= 1) ? _l : 2 - _l;
    _l /= 2;

    return {
        hue: _h,
        saturation: _s,
        lightness: _l
    };
}

function round_with_postfix(v, molt, postfix) {
    if (is_string(v)) {
        return v
    }
    return Math.round(v*molt) + (postfix || '')
}

export function hsl_to_css(data) {
    var s = data.saturation;
    var l = data.lightness;
    var h = data.hue;
    return 'hsl('+ round_with_postfix(h, 360) +', '+ round_with_postfix(s, 100, '%') +', '+ round_with_postfix(l, 100, '%')+')'
}

export function hsb_to_css(data) {
    return hsl_to_css(hsb_to_hsl(data))
}

export function hsb_to_css_with_lightness(data, lightness = 0.5) {

    data.lightness = lightness

    return hsl_to_css(data)
}