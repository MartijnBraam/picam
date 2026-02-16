package api

import "encoding/json"

type StateRGBL struct {
	Red   float32 `json:"red"`
	Green float32 `json:"green"`
	Blue  float32 `json:"blue"`
	Luma  float32 `json:"luma"`
}

type StateGain struct {
	Gain float32 `json:"gain"`
}

type StateShutter struct {
	ContinuousShutterAutoExposure bool    `json:"continuousShutterAutoExposure"`
	ShutterSpeed                  int     `json:"shutterSpeed"`
	ShutterAngle                  float32 `json:"shutterAngle"`
}

type StateWhiteBalance struct {
	WhiteBalance int `json:"whiteBalance"`
}

type StateAutoExposure struct {
	Mode string `json:"mode"`
	Type string `json:"type"`
}

type State struct {
	Gain         StateGain
	Shutter      StateShutter
	WhiteBalance StateWhiteBalance
	AutoExposure StateAutoExposure

	CCLift   StateRGBL
	CCGamma  StateRGBL
	CCGain   StateRGBL
	CCOffset StateRGBL
}

type WebsocketMessage struct {
	Type string      `json:"type"`
	Data interface{} `json:"data"`
}

type ListProperties struct {
	Action     string   `json:"action"`
	Properties []string `json:"properties"`
}
type PropertyChanged struct {
	Action   string      `json:"action"`
	Property string      `json:"property"`
	Value    interface{} `json:"value"`
}

func (s *APIServer) BroadcastMessage(message *WebsocketMessage) {
	t, err := json.Marshal(message)
	if err != nil {
		panic(err)
	}
	s.hub.broadcast <- t
}

func (s *APIServer) SetSensorState(gaina float32, gaind float32, exposure uint32, temperature uint32) {
	s.state.Gain.Gain = gaina
	s.state.Shutter.ShutterSpeed = int(1000000 / exposure)
	s.state.WhiteBalance.WhiteBalance = int(temperature)

	s.BroadcastMessage(&WebsocketMessage{
		Type: "event",
		Data: &PropertyChanged{
			Action:   "propertyValueChanged",
			Property: "/video/gain",
			Value:    s.state.Gain,
		},
	})

	s.BroadcastMessage(&WebsocketMessage{
		Type: "event",
		Data: &PropertyChanged{
			Action:   "propertyValueChanged",
			Property: "/video/shutter",
			Value:    s.state.Shutter,
		},
	})

	s.BroadcastMessage(&WebsocketMessage{
		Type: "event",
		Data: &PropertyChanged{
			Action:   "propertyValueChanged",
			Property: "/video/whiteBalance",
			Value:    s.state.WhiteBalance,
		},
	})
}

func (s *APIServer) SetControls(aeEnable bool, awbEnable bool) {
	if aeEnable {
		s.state.AutoExposure.Mode = "Continuous"
	} else {
		s.state.AutoExposure.Mode = "Off"
	}

	s.BroadcastMessage(&WebsocketMessage{
		Type: "event",
		Data: &PropertyChanged{
			Action:   "propertyValueChanged",
			Property: "/video/autoExposure",
			Value:    s.state.AutoExposure,
		},
	})
}
