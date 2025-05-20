# Environment selector
param (
    [Parameter(Mandatory=$true)]
    [ValidateSet('cpu','cuda','quantum')]
    $mode,
    [ValidateSet('standard','quantum','frontier')]
    $security_level = 'standard',
    [ValidateSet('arbitrage','nft','liquidity','sentiment')]
    $features
)

if ($mode -eq 'cpu') {
    .\.venv_cpu\Scripts\activate
} elseif ($mode -eq 'cuda') {
    conda activate bumbot_cuda
} else {
    # Add quantum environment activation if needed
}

$env:QUANTUM_SECURITY = $security_level
$env:QUANTUM_FRONTIER = $features
python src/main.py
