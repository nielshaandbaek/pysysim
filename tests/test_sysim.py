import sysim

class Level2(sysim.Module):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clk_i = sysim.input(sysim.Bit)
        self.clk_o = sysim.output(sysim.Bit)

    @sysim.process
    def run(self):
        while True:
            yield self.clk_i.event()
            self.clk_o.assign(self.clk_i.value, 1e-9)

class Level1(sysim.Module):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clk_i = sysim.input(sysim.Bit)
        self.clk_o = sysim.output(sysim.Bit)

        self.i_level2 = Level2()
        self.i_level2.clk_i.bind(self.clk_i)
        self.i_level2.clk_o.bind(self.clk_o)

class Register(sysim.Module):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clk_i = sysim.input(sysim.Bit)
        self.d_i = sysim.input(sysim.Int)
        self.q_o = sysim.output(sysim.Int)

    @sysim.process
    def run(self):
        while True:
            yield self.clk_i.rising_edge()
            self.q_o.assign(self.d_i.value)

class Counter(sysim.Module):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clk_i = sysim.input(sysim.Bit)
        self.cnt_o = sysim.output(sysim.Int)

    @sysim.process
    def run(self):
        self.cnt_o.assign(0)

        while True:
            yield self.clk_i.rising_edge()
            self.cnt_o.assign(self.cnt_o.value + 1)

class Composite(sysim.TypeBase):
    def __init__(self, size):
        super().__init__('reg', [size, size])

    def conv(self, value):
        return [x+1 for x in value]

class TB(sysim.Module):
    def __init__(self):
        super().__init__()
        self.clk = sysim.signal(sysim.Bit, 0)
        self.clk_tmp = sysim.signal(sysim.Bit)
        self.cnt = sysim.signal(sysim.Int)
        self.cnt_r = sysim.signal(sysim.Int)
        self.string_r = sysim.signal(sysim.String(8))
        self.reg_r = sysim.signal(Composite(8))

        self.i_cnt = Counter()
        self.i_cnt.clk_i.bind(self.clk)
        self.i_cnt.cnt_o.bind(self.cnt)

        self.i_level = Level1()
        self.i_level.clk_i.bind(self.clk)
        self.i_level.clk_o.bind(self.clk_tmp)

        self.i_reg = Register()
        self.i_reg.clk_i.bind(self.clk_tmp)
        self.i_reg.d_i.bind(self.cnt)
        self.i_reg.q_o.bind(self.cnt_r)

    @sysim.process
    def initial(self):
        self.string_r <<= "deadbeef"
        self.reg_r <<= (0, 0)
        yield sysim.wait(10e-9)
        self.reg_r <<= (127, 128)
        self.string_r <<= "fooobaar"

    @sysim.process
    def clock(self):
        while True:
            self.clk.assign(1)
            yield sysim.wait(10e-9)
            self.clk.assign(0)
            yield sysim.wait(10e-9)

class BindingTB(sysim.Module):
    def __init__(self):
        super().__init__()
        self.clk = sysim.signal(sysim.Bit, 0)
        self.cnt = [sysim.signal(sysim.Int) for _ in range(100)]

        self.i_cnt = [Counter(clk_i=self.clk, cnt_o=self.cnt[i]) for i in range(100)]

    @sysim.process
    def clock(self):
        while True:
            self.clk.assign(1)
            yield sysim.wait(10e-9)
            self.clk.assign(0)
            yield sysim.wait(10e-9)

class DelayTB(sysim.Module):
    def __init__(self):
        super().__init__()
        self.clk = sysim.signal(sysim.Bit, 0)
        self.cnt = sysim.signal(sysim.Int)

        self.i_cnt = Counter(clk_i=self.clk, cnt_o=self.cnt)

    @sysim.process
    def initial(self):
        for _ in range(5):
            self.clk.assign(1, 20e-9)
            yield sysim.wait(10e-9)
            self.clk.assign(0, 20e-9)
            yield sysim.wait(10e-9)

        for _ in range(5):
            self.clk.assign(1)
            yield sysim.wait(10e-9)
            self.clk.assign(0)
            yield sysim.wait(10e-9)

def test_sysim():
    tb = TB()
    sysim.initialize(tb, 1e-9)
    sysim.run(100e-9)
    assert tb.cnt_r.value == 5

def test_sysim_logger():
    tb = TB()
    logger = sysim.VcdLogger("test_logger.vcd")
    sysim.initialize(tb, 1e-9, logger)
    sysim.run(100e-9)
    logger.flush()
    assert tb.cnt_r.value == 5

def test_binding():
    tb = BindingTB()
    sysim.initialize(tb, 1e-9)
    sysim.run(100e-9)
    for i in range(100):
        assert tb.cnt[i].value == 5

def test_delay():
    tb = DelayTB()
    logger = sysim.VcdLogger("test_delay.vcd")
    sysim.initialize(tb, 1e-9, logger)
    sysim.run(200e-9)
    assert tb.cnt.value == 5
