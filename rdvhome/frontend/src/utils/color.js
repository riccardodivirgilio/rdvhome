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

export function hsl_to_hsb(h) {
    var s = data.saturation
    var l = data.lightness
    var h = data.hue;

    var _h = h,
        _s,
        _v;

    l *= 2;
    s *= (l <= 1) ? l : 2 - l;
    _v = (l + s) / 2;
    _s = (2 * s) / (l + s);

    return {
        hue: _h,
        saturation: _s,
        brightness: _v
    };
}

export function hsl_to_css(data) {
    var s = data.saturation;
    var l = data.lightness;
    var h = data.hue;
    return 'hsl('+ Math.round(h*360) +', '+ Math.round(s*100) +'%, '+ Math.round(l*100)+'%)'
}

export function hsb_to_css(data) {
    return hsl_to_css(hsb_to_hsl(data))
}

export function hsb_to_css_with_lightness(data, lightness = 0.5) {

    var hsl = hsb_to_hsl(data)
    data.lightness = lightness

    return hsl_to_css(data)
}