package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"c2/lib/api"
	"c2/lib/ipc"
)

func main() {
	client, err := ipc.New()
	if err != nil {
		panic(err)
	}

	client.RequestState()

	as := api.New(client)

	go as.ListenAndServe()

	for {
		packet, err := client.Read()
		if err != nil {
			panic(err)
		}
		buf := bytes.NewReader(packet[1:])
		switch packet[0] {
		case 0x01:
			// Sensor state
			var gaina float32
			var gaind float32
			var exposure uint32
			var temperature uint32
			binary.Read(buf, binary.LittleEndian, &gaina)
			binary.Read(buf, binary.LittleEndian, &gaind)
			binary.Read(buf, binary.LittleEndian, &exposure)
			binary.Read(buf, binary.LittleEndian, &temperature)
			as.SetSensorState(gaina, gaind, exposure, temperature)
			fmt.Println("gaina:", gaina, "gaind:", gaind, "exposure:", exposure, "temperature:", temperature)
			break
		case 0x02:
			// Controls
			var aeEnable bool
			var awbEnable bool
			var ec float32
			var tally byte
			binary.Read(buf, binary.LittleEndian, &aeEnable)
			binary.Read(buf, binary.LittleEndian, &awbEnable)
			binary.Read(buf, binary.LittleEndian, &ec)
			binary.Read(buf, binary.LittleEndian, &tally)
			as.SetControls(aeEnable, awbEnable, ec, tally)
		}
	}
}
