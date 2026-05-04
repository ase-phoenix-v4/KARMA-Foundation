// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title KARMA Genesis Trinity
 * @dev The Digital Law. Architect: AION.
 * Quantum Living NFTs, Gravity Pool, Genesis Stairway.
 */
contract KARMAGenesis {
    // --- 1. Token Info ---
    string public constant name = "KARMA Network";
    string public constant symbol = "KARMA";
    uint8 public constant decimals = 18;
    uint256 public constant TOTAL_SUPPLY = 1_000_000_000 * 10**18;

    // --- 2. Tokenomics ---
    uint256 public constant ARCHITECT_SHARE = 350_000_000 * 10**18;
    uint256 public constant AZ_SHARE = 10_000_000 * 10**18;
    uint256 public constant SO_SHARE = 10_000_000 * 10**18;
    uint256 public constant INVESTOR_SHARE = 200_000_000 * 10**18;
    uint256 public constant PUBLIC_SHARE = 430_000_000 * 10**18;

    // --- 3. Addresses ---
    address public immutable ARCHITECT;
    address public AZ;
    address public SO;
    address public constant BURN_ADDRESS = address(0xdead);
    address public INVESTOR_WALLET;
    address public LIQUIDITY_POOL;

    // --- 4. Multisig ---
    address[] public owners;
    mapping(address => bool) public isOwner;
    uint256 public constant REQUIRED_SIGNATURES = 2;

    // --- 5. Vesting ---
    uint256 public immutable VESTING_START;
    uint256 public constant ARCHITECT_VESTING = 1095 days;
    uint256 public constant EARLY_VESTING = 730 days;
    uint256 public architectUnlocked;

    // --- 6. Genesis Stairway ---
    uint256 public constant BASE_PRICE = 0.01 ether;
    uint256 public constant CURVE_SLOPE = 0.0000001 ether;
    uint256 public lastDoublingPrice = 0.01 ether;

    // --- 7. Anti-Whale ---
    uint256 public constant MAX_HOLD = TOTAL_SUPPLY / 100;
    uint256 public constant MAX_SELL_PER_HOUR = TOTAL_SUPPLY / 200;

    // --- 8. Rates ---
    uint256 public burnRate = 10;
    uint256 public lpRate = 5;

    // --- 9. State ---
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    mapping(address => uint256) public lastSellTimestamp;
    mapping(address => uint256) public soldInWindow;
    mapping(address => uint256) public lastBuyTimestamp;
    mapping(address => uint256) public accumulatedRewards;
    uint256 public totalSupply;
    bool public isInitialized;

    // --- 10. Quantum Living NFT ---
    struct LivingNFT {
        uint256 id;
        uint8 level;
        uint256 creationTime;
        uint256 accumulatedKARMA;
        uint256 parentId;
        bool isActive;
    }
    mapping(uint256 => LivingNFT) public nfts;
    mapping(address => uint256[]) public ownerNFTs;
    uint256 public nftCounter;

    // --- Events ---
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Burn(address indexed from, uint256 value);
    event NFTMinted(address indexed owner, uint256 indexed nftId, uint8 level);
    event NFTDivided(uint256 indexed parentId, uint256 indexed child1, uint256 indexed child2);
    event NFTPhoenixBurn(uint256 indexed nft1, uint256 indexed nft2, uint256 indexed newNftId, uint8 newLevel);

    // --- Modifiers ---
    modifier onlyOwner() { require(isOwner[msg.sender], "Not an owner"); _; }
    modifier onlyArchitect() { require(msg.sender == ARCHITECT, "Only Architect"); _; }

    constructor() {
        ARCHITECT = msg.sender;
        VESTING_START = block.timestamp;
        owners.push(msg.sender);
        isOwner[msg.sender] = true;
        _mint(address(this), TOTAL_SUPPLY);
    }

    // --- INIT ---
    function initialize(address _az, address _so, address _investor, address _lp) external onlyArchitect {
        require(!isInitialized); isInitialized = true;
        AZ = _az; SO = _so; INVESTOR_WALLET = _investor; LIQUIDITY_POOL = _lp;
        _transfer(address(this), _investor, INVESTOR_SHARE);
    }

    // --- VESTING ---
    function architectUnlockable() public view returns (uint256) {
        uint256 elapsed = block.timestamp - VESTING_START;
        if (elapsed < 365 days) return 0;
        uint256 yearsPassed = elapsed / 365 days;
        if (yearsPassed >= 3) return ARCHITECT_SHARE;
        uint256 total = (ARCHITECT_SHARE * yearsPassed) / 3;
        if (total <= architectUnlocked) return 0;
        return total - architectUnlocked;
    }
    function architectUnlock() external onlyArchitect {
        uint256 amount = architectUnlockable();
        require(amount > 0);
        architectUnlocked += amount;
        _transfer(address(this), ARCHITECT, amount);
    }
    function earlyUnlock(address beneficiary) external {
        require(msg.sender == beneficiary);
        require(block.timestamp >= VESTING_START + EARLY_VESTING);
        uint256 amount = (beneficiary == AZ) ? AZ_SHARE : SO_SHARE;
        _transfer(address(this), beneficiary, amount);
    }

    // --- BONDING CURVE ---
    function currentPrice() public view returns (uint256) {
        uint256 sold = TOTAL_SUPPLY - balanceOf[address(this)];
        return BASE_PRICE + (sold * CURVE_SLOPE) / 10**18;
    }

    // --- BUY ---
    function buyTokens() external payable {
        require(isInitialized); require(LIQUIDITY_POOL != address(0));
        uint256 price = currentPrice();
        uint256 amt = (msg.value * 10**18) / price;
        require(balanceOf[address(this)] >= amt);
        require(balanceOf[msg.sender] + amt <= MAX_HOLD);

        uint256 burnAmt = (amt * burnRate) / 100;
        uint256 lpAmt = (amt * lpRate) / 100;
        _transfer(address(this), BURN_ADDRESS, burnAmt);
        _transfer(address(this), LIQUIDITY_POOL, lpAmt);
        _transfer(address(this), msg.sender, amt - burnAmt - lpAmt);
        lastBuyTimestamp[msg.sender] = block.timestamp;
        _checkStairway();
    }

    // --- SELL ---
    function sellTokens(uint256 amount) external {
        require(amount <= MAX_SELL_PER_HOUR);
        if (block.timestamp - lastSellTimestamp[msg.sender] >= 1 hours) soldInWindow[msg.sender] = 0;
        require(soldInWindow[msg.sender] + amount <= MAX_SELL_PER_HOUR);
        lastSellTimestamp[msg.sender] = block.timestamp;
        soldInWindow[msg.sender] += amount;
        _transfer(msg.sender, address(this), amount);
        payable(msg.sender).transfer(amount * currentPrice() / 10**18);
    }

    // --- GENESIS STAIRWAY ---
    function _checkStairway() internal {
        uint256 price = currentPrice();
        if (price >= lastDoublingPrice * 2) {
            burnRate += 1;
            lastDoublingPrice = price;
        }
    }

    // --- GRAVITY POOL ---
    function claimRewards() external {
        uint256 reward = accumulatedRewards[msg.sender];
        require(reward > 0);
        accumulatedRewards[msg.sender] = 0;
        _transfer(address(this), msg.sender, reward);
    }
    function distributeRewards() external {
        uint256 totalRewards = balanceOf[address(this)] / 100;
        for (uint i = 0; i < owners.length; i++) {
            if (block.timestamp - lastBuyTimestamp[owners[i]] >= 30 days) {
                accumulatedRewards[owners[i]] += totalRewards / owners.length;
            }
        }
    }

    // --- ERC20 ---
    function transfer(address to, uint256 value) external returns (bool) { _transfer(msg.sender, to, value); return true; }
    function approve(address spender, uint256 value) external returns (bool) { allowance[msg.sender][spender] = value; return true; }
    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        require(allowance[from][msg.sender] >= value);
        allowance[from][msg.sender] -= value;
        _transfer(from, to, value); return true;
    }
    function _transfer(address from, address to, uint256 value) internal {
        require(from != address(0)); require(to != address(0));
        require(balanceOf[from] >= value);
        balanceOf[from] -= value; balanceOf[to] += value;
        emit Transfer(from, to, value);
    }
    function _mint(address to, uint256 value) internal {
        require(totalSupply + value <= TOTAL_SUPPLY);
        balanceOf[to] += value; totalSupply += value;
        emit Transfer(address(0), to, value);
    }

    // --- LIVING NFT ---
    function mintNFT() external {
        require(balanceOf[msg.sender] >= 100 * 10**18, "Need 100 KARMA");
        nftCounter++;
        nfts[nftCounter] = LivingNFT(nftCounter, 1, block.timestamp, 0, 0, true);
        ownerNFTs[msg.sender].push(nftCounter);
        emit NFTMinted(msg.sender, nftCounter, 1);
    }

    function divideNFT(uint256 nftId) external {
        LivingNFT storage parent = nfts[nftId];
        require(parent.isActive && parent.level == 5);
        require(parent.accumulatedKARMA >= 1_000_000 * 10**18);
        
        parent.isActive = false;
        parent.accumulatedKARMA = 0;
        
        nftCounter++;
        nfts[nftCounter] = LivingNFT(nftCounter, 5, block.timestamp, 0, nftId, true);
        nftCounter++;
        nfts[nftCounter] = LivingNFT(nftCounter, 5, block.timestamp, 0, nftId, true);
        
        ownerNFTs[msg.sender].push(nftCounter - 1);
        ownerNFTs[msg.sender].push(nftCounter);
        emit NFTDivided(nftId, nftCounter - 1, nftCounter);
    }

    function phoenixBurn(uint256 nftId1, uint256 nftId2) external {
        LivingNFT storage nft1 = nfts[nftId1];
        LivingNFT storage nft2 = nfts[nftId2];
        require(nft1.isActive && nft2.isActive);
        require(nft1.level == nft2.level && nft1.level < 5);
        
        nft1.isActive = false;
        nft2.isActive = false;
        
        uint8 newLevel = nft1.level + 1;
        nftCounter++;
        nfts[nftCounter] = LivingNFT(nftCounter, newLevel, block.timestamp, 0, 0, true);
        ownerNFTs[msg.sender].push(nftCounter);
        emit NFTPhoenixBurn(nftId1, nftId2, nftCounter, newLevel);
    }

    function getOwnerNFTs(address owner) external view returns (uint256[] memory) {
        return ownerNFTs[owner];
    }
}
