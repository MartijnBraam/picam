package api

import (
	"encoding/json"
	"net/http"
)

type CodecFormat struct {
	Codec     string `json:"codec"`
	Container string `json:"container"`
}

type VideoFormat struct {
	Name       string `json:"name"`
	FrameRate  string `json:"frameRate"`
	Width      int    `json:"width"`
	Height     int    `json:"height"`
	Interlaced bool   `json:"interlaced"`
}

type SystemResponse struct {
	CodecFormat CodecFormat `json:"codecFormat"`
	VideoFormat VideoFormat `json:"videoFormat"`
}

func (s *APIServer) GetSystem(w http.ResponseWriter, r *http.Request) {
	response := SystemResponse{
		CodecFormat: CodecFormat{
			Codec:     "H.264",
			Container: "MPEG2-TS",
		},
		VideoFormat: VideoFormat{
			Name:       "1080p30",
			FrameRate:  "30.00",
			Width:      1920,
			Height:     1080,
			Interlaced: false,
		},
	}

	enc := json.NewEncoder(w)
	enc.Encode(response)
}
