function ajax(path, callback) {
    fetch("http://192.168.2.34:8000/control/api/v1" + path, {
        method: "GET",
        headers: {
            'Content-type': 'application/json'
        }
    })
        .then((response) => {
            if (!response.ok) {
                thorw
                Error(response.statusText);
            }
            return response;
        })
        .then((response) => response.json())
        .then((data) => {
            callback(data)
        })
        .catch((error) => {
            console.error(error);
        })
}

function Binding(state, key) {
    const _this = this;
    this.value = state[key];
    if (this.value === undefined) {
        this.value = {};
    }
    this.bindings = [];

    this.valueGetter = function () {
        return _this.value;
    }
    this.valueSetter = function (val) {
        console.log("Set value to ", val);
        _this.value = val;
        for (let i = 0; i < _this.bindings.length; i++) {
            _this.bindings[i](val);
        }
    }
    this.onChange = function (callback) {
        this.bindings.push(callback);
        return _this;
    }

    Object.defineProperty(state, key, {
        get: this.valueGetter,
        set: this.valueSetter,
    });

    state[key] = this.value;
}

let properties = {};

document.addEventListener("DOMContentLoaded", function () {
    ajax("/system", function (data) {
        window.mode.innerHTML = "<span>" + data.videoFormat.name + "</span>";
        window.shutter.min = data.videoFormat.frameRate;
    });
    const ws = new WebSocket("http://192.168.2.34:8000/control/api/v1/event/websocket");

    new Binding(properties, "/video/whiteBalance").onChange(function (data) {
        window.whitebalance.value = data.whiteBalance;
        window.whitebalanceLabel.innerText = data.whiteBalance + "k";
    })
    window.whitebalance.oninput = function (el) {
        const val = el.value;
        ajax("/video/whiteBalance")
    }

    new Binding(properties, "/video/gain").onChange(function (data) {
        window.gain.value = data.gain;
        window.gainLabel.innerText = Math.round(data.gain) + " dB";
    })

    new Binding(properties, "/video/shutter").onChange(function (data) {
        console.error(data);
        window.shutter.value = data.shutterSpeed;
        window.shutterLabel.innerText = "1/" + data.shutterSpeed;
    })


    ws.onopen = (event) => {
        console.log("Event socket opened");
        ws.send(JSON.stringify({type: "request", data: {action: "listProperties"}}));
    }
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("Message", data);
        if (data.type === "event") {
            if (data.data.action === "propertyValueChanged") {
                let old = properties[data.data.property];
                if (old === undefined) {
                    return;
                }
                Object.assign(old, data.data.value);
                properties[data.data.property] = old;
            }
        } else if (data.type === "response") {
            if (data.data.action === "listProperties") {
                for (let i = 0; i < data.data.properties.length; i++) {
                    ws.send(JSON.stringify({
                        type: "request",
                        data: {action: "subscribe", properties: [data.data.properties[i]]}
                    }));
                }
            }
        }
    }
});