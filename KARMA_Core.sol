// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract KARMANetwork {
    string public constant name = "KARMA Network";
    string public constant symbol = "KARMA";
    uint8 public constant decimals = 18;
    uint256 public constant TOTAL_SUPPLY = 1_000_000_000 * 10**18;
    uint256 public constant ARCHITECT_SHARE = 300_000_000 * 10**18;
    uint256 public constant IGOR_SHARE = 10_000_000 * 10**18;
    uint256 public constant TEAM_SHARE = 50_000_000 * 10**18;
    uint256 public constant INVESTOR_SHARE = 200_000_000 * 10**18;
    uint256 public constant PUBLIC_SHARE = 200_000_000 * 10**18;
    uint256 public constant DAO_SHARE = 240_000_000 * 10**18;
    address public immutable ARCHITECT;
    address public IGOR;
    address public constant BURN = address(0xdead);
    address public TEAM_WALLET;
    address public INVESTOR_WALLET;
    address public DAO_WALLET;
    address public LP;
    address[] public owners;
    mapping(address => bool) public isOwner;
    uint256 public immutable START;
    uint256 public unlocked;
    uint256 public constant PRICE = 0.0001 ether;
    uint256 public constant SLOPE = 0.00000001 ether;
    uint256 public constant MAX_H = TOTAL_SUPPLY / 100;
    uint256 public constant MAX_S = TOTAL_SUPPLY / 200;
    uint256 public burnRate = 10;
    uint256 public lpRate = 5;
    uint256 public constant APY = 25;
    uint256 public rewards;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    mapping(address => uint256) public lastSell;
    mapping(address => uint256) public sold;
    uint256 public totalSupply;
    bool public init;
    
    modifier onlyOwner() { require(isOwner[msg.sender]); _; }
    
    constructor() {
        ARCHITECT = msg.sender;
        START = block.timestamp;
        owners.push(msg.sender);
        isOwner[msg.sender] = true;
        balanceOf[address(this)] = TOTAL_SUPPLY;
        totalSupply = TOTAL_SUPPLY;
    }
    
    function initialize(address igor, address team, address inv, address dao, address _lp) external {
        require(msg.sender == ARCHITECT); require(!init); init = true;
        IGOR = igor; TEAM_WALLET = team; INVESTOR_WALLET = inv; DAO_WALLET = dao; LP = _lp;
        _send(team, TEAM_SHARE); _send(inv, INVESTOR_SHARE); _send(dao, DAO_SHARE);
    }
    
    function _send(address to, uint256 val) internal {
        balanceOf[address(this)] -= val; balanceOf[to] += val;
    }
    
    function currentPrice() public view returns (uint256) {
        uint256 soldTokens = TOTAL_SUPPLY - balanceOf[address(this)];
        return PRICE + (soldTokens * SLOPE) / 10**18;
    }
    
    function buy() external payable {
        require(init); require(LP != address(0));
        uint256 amt = (msg.value * 10**18) / currentPrice();
        require(balanceOf[address(this)] >= amt);
        require(balanceOf[msg.sender] + amt <= MAX_H);
        uint256 b = (amt * burnRate) / 100;
        uint256 l = (amt * lpRate) / 100;
        _send(BURN, b); _send(LP, l);
        _send(msg.sender, amt - b - l);
    }
    
    function sell(uint256 amt) external {
        require(amt <= MAX_S);
        if (block.timestamp - lastSell[msg.sender] >= 1 hours) sold[msg.sender] = 0;
        require(sold[msg.sender] + amt <= MAX_S);
        lastSell[msg.sender] = block.timestamp;
        sold[msg.sender] += amt;
        balanceOf[msg.sender] -= amt; balanceOf[address(this)] += amt;
        payable(msg.sender).transfer(amt * currentPrice() / 10**18);
    }
    
    function transfer(address to, uint256 val) external returns (bool) {
        balanceOf[msg.sender] -= val; balanceOf[to] += val; return true;
    }
    
    function approve(address s, uint256 v) external returns (bool) {
        allowance[msg.sender][s] = v; return true;
    }
    
    function transferFrom(address f, address t, uint256 v) external returns (bool) {
        require(allowance[f][msg.sender] >= v);
        allowance[f][msg.sender] -= v;
        balanceOf[f] -= v; balanceOf[t] += v; return true;
    }
}
