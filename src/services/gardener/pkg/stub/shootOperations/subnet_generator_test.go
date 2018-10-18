package shootOperations

import (
	"net"
	"testing"
)

func TestSubnetGenerator_0SizeCausesError(t *testing.T) {
	_, err := genBestFittingSNWithinSubnet("192.1.1.0/16", 0)
	if err == nil {
		t.Errorf("zero size should cause error")
	}
}

func TestSubnetGenerator_InvalidCidrCausesError(t *testing.T) {
	cidrs := []string{"", "foo", "192.168.1.4", "192.168.1.4/999999"}
	for _, cidr := range cidrs {
		_, err := genBestFittingSNWithinSubnet(cidr, 1)
		if err == nil {
			t.Errorf("invalid cidr should cause error")
		}
	}
}

func TestSubnetGenerator_TooBigRequestCausesError(t *testing.T) {
	_, err := genBestFittingSNWithinSubnet("192.1.1.1/30", 1<<33)
	if err == nil {
		t.Errorf("request was too big, should cause error")
	}
}

func TestSubnetGenerator_Simple(t *testing.T) {
	tests := []struct {
		cidr     string
		size     int
		expected string
	}{
		{"192.1.1.0/16", 1, "192.1.0.0/30"},
		{"192.2.1.0/16", 1, "192.2.0.0/30"},
		{"192.1.0.0/16", 2, "192.1.0.0/30"},
		{"192.1.0.0/16", 3, "192.1.0.0/29"},
		{"192.1.0.0/16", 6, "192.1.0.0/29"},
	}

	for _, test := range tests {
		sn, err := genBestFittingSNWithinSubnet(test.cidr, test.size)
		if err != nil {
			t.Fatalf(err.Error())
		}

		_, net, err := net.ParseCIDR(sn)
		if err != nil {
			t.Fatalf("invalid cidr: %s", err.Error())
		}

		ones, bits := net.Mask.Size()
		nFreeAddr := 1 << uint64(bits-ones)
		nFreeAddr -= 2 // last and first address in ip range are reserved
		if nFreeAddr < 1 {
			t.Errorf("returned subnet is too small. nfree: %d, want: %d", nFreeAddr, 1)
		}

		if sn != test.expected {
			t.Fatalf("invalid subnet. size: %d, expected: %s, got: %s", test.size, test.expected, sn)
		}
	}
}

func TestGenerateNextFreeSubnet_NextCidrRequiresSameAmountOfBits(t *testing.T) {
	tests := []struct {
		cidr     string
		size     int
		expected string
	}{
		{"192.1.0.0/30", 1, "192.1.0.4/30"},
		{"192.2.0.0/30", 1, "192.2.0.4/30"},
		{"192.2.0.0/30", 4, "192.2.0.8/29"}, // corner case: first and last address are reserved and must be considered
		{"192.1.0.0/29", 6, "192.1.0.8/29"},
		{"192.1.0.0/29", 8, "192.1.0.16/28"}, // corner case: first and last address are reserved and must be considered
		{"192.1.0.0/29", 9, "192.1.0.16/28"},
	}

	for _, test := range tests {
		sn, err := generateNextFreeSubnet(test.cidr, test.size)
		if err != nil {
			t.Fatalf(err.Error())
		}

		_, net, err := net.ParseCIDR(sn)
		if err != nil {
			t.Fatalf("invalid cidr: %s", err.Error())
		}

		ones, bits := net.Mask.Size()
		nFreeAddr := 1 << uint64(bits-ones)
		nFreeAddr -= 2 // last and first address in ip range are reserved
		if nFreeAddr < 1 {
			t.Errorf("returned subnet is too small. nfree: %d, want: %d", nFreeAddr, 1)
		}

		if sn != test.expected {
			t.Fatalf("invalid subnet. size: %d, expected: %s, got: %s", test.size, test.expected, sn)
		}
	}
}

func TestGenerateNextFreeSubnet_NextCidrRequiresMoreBits(t *testing.T) {
	tests := []struct {
		cidr     string
		size     int
		expected string
	}{
		{"192.1.0.0/30", 5, "192.1.0.8/29"},
		{"192.2.0.0/30", 5, "192.2.0.8/29"},
		{"192.1.1.0/30", 5, "192.1.1.8/29"},
		{"192.1.0.0/30", 6, "192.1.0.8/29"},
		{"192.1.0.0/30", 8, "192.1.0.16/28"},
	}

	for _, test := range tests {
		sn, err := generateNextFreeSubnet(test.cidr, test.size)
		if err != nil {
			t.Fatalf(err.Error())
		}

		_, net, err := net.ParseCIDR(sn)
		if err != nil {
			t.Fatalf("invalid cidr: %s", err.Error())
		}

		ones, bits := net.Mask.Size()
		nFreeAddr := 1 << uint64(bits-ones)
		nFreeAddr -= 2 // last and first address in ip range are reserved
		if nFreeAddr < 1 {
			t.Errorf("returned subnet is too small. nfree: %d, want: %d", nFreeAddr, 1)
		}

		if sn != test.expected {
			t.Fatalf("expected: %s, got: %s", test.expected, sn)
		}
	}
}

func TestGenerateNextFreeSubnet_NoNextFreeSubnetAvailable(t *testing.T) {
	tests := []struct {
		cidr string
		size int
	}{
		{"255.255.255.1/24", 1 << 16},
		{"255.255.0.0/24", 1 << 16},
		{"255.255.255.255/32", 1},
	}

	for _, test := range tests {
		sn, err := generateNextFreeSubnet("255.255.255.255/32", 1)
		if err == nil {
			t.Fatalf("should return error for sn '%s' and size %d, but got: %s", test.cidr, test.size, sn)
		}
	}
}

func TestFancySubnetGenerator_GenerateSubnet(t *testing.T) {
	sng := NewSubnetGenerator("250.0.0.0/16")

	subnets := make(map[string]struct{})
	for i := 0; i < 1000; i++ {
		sn, err := sng.GenerateSubnet(1)
		if err != nil {
			t.Fatalf("error on iteration %d. err: %s", i, err)
		} else if _, ok := subnets[sn]; ok {
			t.Fatalf("subnet %s already exists!", sn)
		} else {
			subnets[sn] = struct{}{}
		}
	}
}

func TestFancySubnetGenerator_Generate24Subnet(t *testing.T) {
	sng := NewSubnetGenerator("250.0.0.0/16")

	sn, err := sng.GenerateNext24Subnet()
	if err != nil {
		t.Fatal(err)
	}

	_, net, err := net.ParseCIDR(sn)
	if err != nil {
		t.Fatal(err)
	}

	ones, _ := net.Mask.Size()
	if ones != 24 {
		t.Fatalf("expected 24 ones, but got %d", ones)
	}
}

func TestFancySubnetGenerator_Generate25Subnet(t *testing.T) {
	sng := NewSubnetGenerator("250.0.0.0/16")

	sn, err := sng.GenerateNext25Subnet()
	if err != nil {
		t.Fatal(err)
	}

	_, net, err := net.ParseCIDR(sn)
	if err != nil {
		t.Fatal(err)
	}

	ones, _ := net.Mask.Size()
	if ones != 25 {
		t.Fatalf("expected 25 ones, but got %d", ones)
	}
}

func TestSubnetGenerator_NextRequestedSnIsSmallerThanPrevious(t *testing.T) {
	sng := NewSubnetGenerator("10.0.0.0/16")
	const internal = "10.0.6.0/24"
	sng.lastSubnet = internal

	worker, _ := sng.GenerateNext25Subnet()

	intIp, intNet, _ := net.ParseCIDR(internal)
	wIp, wNet, _ := net.ParseCIDR(worker)

	if intNet.Contains(wIp) {
		t.Fatalf("newly generated subnet (%s) is covered by previous one (%s)", worker, internal)
	} else if wNet.Contains(intIp) {
		t.Fatalf("old subnet (%s) is covered by new one (%s)", internal, worker)
	}
}

func TestSubnetGenerator_NextRequestedSnIsBiggerThanPrevious(t *testing.T) {
	sng := NewSubnetGenerator("10.0.0.0/16")
	const internal = "10.0.6.0/25"
	sng.lastSubnet = internal

	worker, _ := sng.GenerateNext24Subnet()

	iIp, intNet, _ := net.ParseCIDR(internal)
	wIp, wNet, _ := net.ParseCIDR(worker)

	if intNet.Contains(wIp) {
		t.Fatalf("newly generated subnet (%s) is covered by previous one (%s)", worker, internal)
	} else if wNet.Contains(iIp) {
		t.Fatalf("old subnet (%s) is covered by new one (%s)", internal, worker)
	}
}

func TestSubnetGenerator_Init_Noop(t *testing.T) {
	sng := NewSubnetGenerator("250.0.0.0/16")
	sng.Init(nil)

	if len(sng.lastSubnet) != 0 {
		t.Fatal("nil map modifies!")
	}

	m := make([]*net.IPNet, 0)
	sng.Init(m)
	if len(sng.lastSubnet) != 0 {
		t.Fatal("empty map modifies!")
	}
}

func TestSubnetGenerator_Init_SingleEntry(t *testing.T) {
	sng := NewSubnetGenerator("250.0.0.0/16")
	m := createInputForInit([]string{"250.0.0.0/30"})

	sng.Init(m)

	if sng.lastSubnet != "250.0.0.0/30" {
		t.Fatalf("invalid last subnet. want: '%s', have: '%s'", "250.0.0.0/30", sng.lastSubnet)
	}
}

func createInputForInit(cidrs []string) []*net.IPNet {
	l := make([]*net.IPNet, 0, len(cidrs))
	for _, cidr := range cidrs {
		if _, net, err := net.ParseCIDR(cidr); err != nil {
			panic(err)
		} else {
			l = append(l, net)
		}
	}

	return l
}

func TestSubnetGenerator_Init_MultiEntry(t *testing.T) {
	sng := NewSubnetGenerator("250.0.0.0/16")
	m := createInputForInit([]string{"250.0.0.0/30", "250.0.0.48/28"})

	sng.Init(m)

	want := "250.0.0.48/28"
	if sng.lastSubnet != want {
		t.Fatalf("invalid last subnet. want: '%s', have: '%s'", want, sng.lastSubnet)
	}
}

func TestSubnetGenerator_Init_OverlappingSubnets(t *testing.T) {
	sng := NewSubnetGenerator("250.0.0.0/16")
	m := createInputForInit([]string{"250.0.0.0/30", "250.0.0.0/31"})

	sng.Init(m)

	want := "250.0.0.0/30"
	if sng.lastSubnet != want {
		t.Fatalf("invalid last subnet. want: '%s', have: '%s'", want, sng.lastSubnet)
	}
}
