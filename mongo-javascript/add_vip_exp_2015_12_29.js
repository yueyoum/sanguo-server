/**
 * Created by wang on 15-12-29.
 */

var vip_exp = function(obj) {
    var purchase_got = 0;
    if (obj.purchase_got != undefined)
    {
        purchase_got = obj.purchase_got;
    }

    db.character.update(
            {_id: obj._id},
            {$set: {
                        purchase_got: purchase_got,
                        vip_exp: purchase_got
                   }}
            );
}

var main = function() {
    db.character.find().forEach(vip_exp);
}

