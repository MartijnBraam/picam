package api

import (
	"encoding/json"
	"net/http"
)

func (s *APIServer) GetVideoAutoExposure(w http.ResponseWriter, r *http.Request) {
	enc := json.NewEncoder(w)
	enc.Encode(s.state.AutoExposure)
}

func (s *APIServer) PutVideoAutoExposure(w http.ResponseWriter, r *http.Request) {
	json.NewDecoder(r.Body).Decode(&s.state.AutoExposure)

	switch s.state.AutoExposure.Mode {
	case "Off":
		s.cam.EnableAutoExposure(false)
	default:
		s.cam.EnableAutoExposure(true)
	}

	s.BroadcastMessage(&WebsocketMessage{
		Type: "event",
		Data: &PropertyChanged{
			Action:   "propertyValueChanged",
			Property: "/video/autoExposure",
			Value:    s.state.AutoExposure,
		},
	})

	enc := json.NewEncoder(w)
	enc.Encode(s.state.AutoExposure)
}

func (s *APIServer) TriggerWhiteBalance(w http.ResponseWriter, r *http.Request) {
	s.cam.DoAutoWhitebalance()
	w.WriteHeader(http.StatusNoContent)
}
