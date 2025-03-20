const versions = document.getElementById('qds-vdropdown');

function resolveVersions(path) {
    var docSet = '';
    var currentVersion = '';
    if (path === undefined || path.length == 0)
        return;
    var parts = path[1].split('-');
    if (parts.length < 2)
        currentVersion = parts[0];
    else
        currentVersion = parts.pop();
    docSet = parts.join('-');
    if (!isNaN(parseInt(docSet.slice(-1), 10)))
        docSet = docSet.slice(0,-1);
    var doc = path.slice(2).join('/');
    fetch('/.versions/' + docSet + '.json')
        .then(data => data.json())
        .then(async function(data) {
            for (var i = 0; i < data.versions.length; i++) {
                const ver = data.versions[i];
                const resp = await fetch(ver.root + doc, { method: 'HEAD' });
                if (resp.ok) {
                    var selected = ver.root.endsWith('-' + currentVersion + '/');
                    versions.append(new Option(ver.name, ver.root, selected, selected));
                }
            }
            if (versions.childElementCount > 0)
                versions.style.visibility = 'visible';
        });
}

(function(){
    if (versions === undefined)
        return;

    var path = window.location.pathname.split('/');
    resolveVersions(path);
    versions.addEventListener('change', function() {
        var hash = window.location.hash;
        var currentPath = window.location.pathname;
        var page = currentPath.split('/').slice(2).join('/');
        window.location = this.value + page + hash;
    });
})();
