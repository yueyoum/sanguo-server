/**
 * Created by wang on 14-9-18.
 */

var mf = function(obj) {
    var tmp = [];
    var pending = [];
    for (var key in obj.friends) {
        if (obj.friends[key] == 2) {tmp.push(parseInt(key));}
        else {pending.push(parseInt(key));}
    }
    db.friend.update({_id: obj._id}, {$unset: {friends: 1}});
    db.friend.update({_id: obj._id}, {$set: {friends: tmp, pending: pending}});
}

var main = function() {
    db.friend.find.forEach(mf);
}
