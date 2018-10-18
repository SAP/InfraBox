package shootOperations

import (
	"encoding/binary"
	"fmt"
	"net"
	"sort"
)

type SubnetGenerator struct {
	baseCIDR   string
	lastSubnet string
}

/**
Generates a new subnet generator. Requires a base subnet (baseCIDR) where all generated subnets will lie in

sng := NewsubnetGenerator("10.250.0.0/16")
blockedCIDRs := map[string]struct{} {"10.250.0.0/24" : struct{}{}, "10.250.1.0/24" : struct{}{}}
nextSn, _ := sng.GenerateSubnet(254)
*/
func NewSubnetGenerator(baseCIDR string) *SubnetGenerator {
	_, _, err := net.ParseCIDR(baseCIDR)
	if err != nil {
		panic(err)
	}

	return &SubnetGenerator{
		baseCIDR: baseCIDR,
	}
}

type ipnetList []*net.IPNet

func (list ipnetList) Len() int      { return len(list) }
func (list ipnetList) Swap(i, j int) { list[i], list[j] = list[j], list[i] }
func (list ipnetList) Less(i, j int) bool {
	iIp := binary.BigEndian.Uint32(list[i].IP)
	jIP := binary.BigEndian.Uint32(list[j].IP)
	if iIp != jIP {
		return iIp < jIP
	}

	return list[j].Contains(list[i].IP) // definition: subnets are 'bigger' if they include more ip addresses
}

// initializes the generator with the given map of CIDRs. After the call, no generated subnet will overlap with
// the ones given in blockedCIDRs
func (sng *SubnetGenerator) Init(blockedCIDRs []*net.IPNet) {
	if (blockedCIDRs == nil) || (len(blockedCIDRs) == 0) {
		return
	}

	sort.Sort(ipnetList(blockedCIDRs))
	sng.lastSubnet = blockedCIDRs[len(blockedCIDRs)-1].String()
}

func (sng *SubnetGenerator) GenerateNext24Subnet() (string, error) {
	return sng.GenerateSubnet(254) // 254 because size means the number of _usable_ ip adresses. The first and last one in a subnet are reserved and not usable.
}

func (sng *SubnetGenerator) GenerateNext25Subnet() (string, error) {
	return sng.GenerateSubnet(126) // 126 because size means the number of _usable_ ip adresses. The first and last one in a subnet are reserved and not usable.
}

func (sng *SubnetGenerator) GenerateSubnet(size int) (string, error) {
	if len(sng.lastSubnet) == 0 {
		sn, err := genBestFittingSNWithinSubnet(sng.baseCIDR, size)
		if err == nil {
			sng.lastSubnet = sn
		}
		return sn, err
	}

	sn, err := generateNextFreeSubnet(sng.lastSubnet, size)
	if err == nil {
		sng.lastSubnet = sn
	}
	return sn, err
}

func genBestFittingSNWithinSubnet(cidr string, size int) (string, error) {
	if size == 0 {
		return "", fmt.Errorf("subnet of size 0 requested")
	}

	_, ipNet, err := net.ParseCIDR(cidr)
	if err != nil {
		return "", err
	}

	nOnes, nBits := ipNet.Mask.Size()
	nFreeAddr := (1 << uint32(nBits-nOnes)) - 2
	nZeroes := uint32(1)
	for nZeroes = 1; ((1 << nZeroes) - 2) < size; nZeroes++ {
	} // -2 because first and last addr in a subnet are reserved
	if nZeroes > 31 {
		return "", fmt.Errorf("too big subnet requested: %d", size)
	}
	nOnes = int(32 - nZeroes)

	if nFreeAddr >= size { // requested size fits into given subnet. Return a smaller subnet if possible
		ipNet.Mask = net.CIDRMask(nOnes, 32)
		return ipNet.String(), nil
	} else {
		return "", fmt.Errorf("should not happen")
	}
}

func generateNextFreeSubnet(lastBlockedCidr string, size int) (string, error) {
	if size == 0 {
		return "", fmt.Errorf("subnet of size 0 requested")
	}

	_, ipNet, err := net.ParseCIDR(lastBlockedCidr)
	if err != nil {
		return "", err
	}

	nZeroes := uint32(1)
	for nZeroes = 1; ((1 << nZeroes) - 2) < size; nZeroes++ {
	}
	if nZeroes > 31 {
		return "", fmt.Errorf("too big subnet requested: %d", size)
	}

	ipNet.IP = nextStartingIP(ipNet, nZeroes)
	nOnes := int(32 - nZeroes)
	ipNet.Mask = net.CIDRMask(nOnes, 32)

	if ipNet.IP.Equal([]byte{0, 0, 0, 0}) {
		return "", fmt.Errorf("no next free subnet available")
	}

	return ipNet.String(), nil
}

func nextStartingIP(oldNet *net.IPNet, nZeroesNewNet uint32) net.IP {
	oldNOnes, _ := oldNet.Mask.Size()
	oldNZeroes := uint32(32 - oldNOnes)
	oIpInt := binary.BigEndian.Uint32(oldNet.IP)
	if oldNZeroes >= nZeroesNewNet { // is the requested new subnet smaller or same-sized to the old one?
		oIpInt = oIpInt >> oldNZeroes
		oIpInt++
		oIpInt = oIpInt << oldNZeroes
	} else {
		oIpInt = oIpInt >> nZeroesNewNet
		oIpInt++
		oIpInt = oIpInt << nZeroesNewNet
	}
	nextStartIp := make([]byte, 4)
	binary.BigEndian.PutUint32(nextStartIp, oIpInt)
	return nextStartIp
}
