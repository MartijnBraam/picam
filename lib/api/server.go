package api

import (
	"embed"
	"io/fs"
	"log"
	"mncam/lib/ipc"
	"net/http"

	"github.com/gorilla/handlers"
	"github.com/gorilla/mux"
)

//go:embed public
var publicFS embed.FS

type APIServer struct {
	srv   http.Server
	mux   *mux.Router
	hub   *Hub
	state *State
	cam   *ipc.IPCClient
}

func New(client *ipc.IPCClient) *APIServer {
	result := &APIServer{state: &State{}, cam: client}
	result.mux = mux.NewRouter()
	result.srv.Addr = "0.0.0.0:8000"
	headersOk := handlers.AllowedHeaders([]string{"*"})
	originsOk := handlers.AllowedOrigins([]string{"*"})
	methodsOk := handlers.AllowedMethods([]string{"GET", "HEAD", "POST", "PUT", "OPTIONS"})

	result.srv.Handler = handlers.CORS(originsOk, headersOk, methodsOk)(result.mux)

	api := result.mux.PathPrefix("/control/api/v1").Subrouter()
	api.HandleFunc("/system", result.GetSystem).Methods("GET")
	api.HandleFunc("/video/autoExposure", result.GetVideoAutoExposure).Methods("GET")
	api.HandleFunc("/video/autoExposure", result.PutVideoAutoExposure).Methods("PUT")

	api.HandleFunc("/video/whiteBalance/doAuto", result.TriggerWhiteBalance).Methods("PUT")

	api.HandleFunc("/event/websocket", result.EventWebsocket)

	// Serve unmatched requests with the embedded static files
	public, _ := fs.Sub(publicFS, "public")
	rootfs := http.FileServerFS(public)
	result.mux.PathPrefix("/").Handler(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// the index.html name is a special case for golang so use home.html instead
		if r.URL.Path == "/" {
			r.URL.Path = "/home.html"
		}
		rootfs.ServeHTTP(w, r)
	})).Methods("GET")

	hub := NewHub()
	go hub.run()
	result.hub = hub

	return result
}

func (s *APIServer) ListenAndServe() error {
	log.Println("Listening on", s.srv.Addr)
	return s.srv.ListenAndServe()
}
